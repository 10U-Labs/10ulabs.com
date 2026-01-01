"""Unit tests for Lambda packaging - validates all imports are included."""
import ast
import re
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT


ENDPOINT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "ecs"
DATA_TF = ENDPOINT_SRC / "data.tf"

# Standard library modules that don't need to be packaged
STDLIB_MODULES = {
    'json', 'logging', 'os', 'time', 'typing', 'urllib', 'sys', 're',
    'collections', 'functools', 'itertools', 'pathlib', 'datetime',
    'contextlib', 'abc', 'copy', 'hashlib', 'base64', 'uuid', 'io',
    'types', 'unittest', 'dataclasses', 'enum', 'warnings',
}

# Installed packages available in Lambda runtime
INSTALLED_PACKAGES = {
    'boto3', 'botocore', 'urllib3',
}


def parse_archive_file_sources(data_tf_content: str) -> dict:
    """Parse data.tf to extract archive_file source mappings.

    Returns a dict mapping filename -> source path (relative or absolute).
    """
    sources = {}

    # Match source blocks within archive_file
    # Pattern: source { content = file("path") filename = "name" }
    source_pattern = re.compile(
        r'source\s*\{[^}]*'
        r'content\s*=\s*file\("([^"]+)"\)[^}]*'
        r'filename\s*=\s*"([^"]+)"[^}]*\}',
        re.DOTALL
    )

    for match in source_pattern.finditer(data_tf_content):
        source_path = match.group(1)
        filename = match.group(2)
        sources[filename] = source_path

    return sources


def get_imports_from_file(file_path: Path) -> set[str]:
    """Parse a Python file and extract all import names."""
    imports: set[str] = set()

    try:
        content = file_path.read_text()
        tree = ast.parse(content)
    except (SyntaxError, FileNotFoundError):
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split('.')[0]
                imports.add(module)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = node.module.split('.')[0]
                imports.add(module)

    return imports


def resolve_source_path(source_path: str, base_dir: Path) -> Path:
    """Resolve a Terraform file() path to an actual file path."""
    resolved = source_path.replace('${path.module}', str(base_dir))
    return Path(resolved).resolve()


def get_packaged_modules() -> dict:
    """Get the modules packaged in the Lambda zip."""
    content = DATA_TF.read_text()
    sources = parse_archive_file_sources(content)

    modules = {}
    for filename, source_path in sources.items():
        if filename.endswith('.py'):
            module_name = filename[:-3]
            resolved_path = resolve_source_path(source_path, ENDPOINT_SRC)
            modules[module_name] = resolved_path

    return modules


def get_missing_imports(source_path: Path, packaged: set) -> list:
    """Get list of imports that are missing from the package."""
    if not source_path.exists():
        return []

    imports = get_imports_from_file(source_path)
    missing = []

    for imp in imports:
        if imp in STDLIB_MODULES:
            continue
        if imp in INSTALLED_PACKAGES:
            continue
        if imp not in packaged:
            missing.append(imp)

    return missing


class TestLambdaPackaging:
    """Tests to validate Lambda package includes all required modules."""

    def test_data_tf_exists(self):
        """Verify data.tf file exists."""
        assert DATA_TF.exists(), f"data.tf not found at {DATA_TF}"

    def test_archive_file_has_sources(self):
        """Verify archive_file has source blocks."""
        packaged = get_packaged_modules()
        assert len(packaged) > 0, "No source blocks found in archive_file"

    def test_handler_is_packaged(self):
        """Verify handler.py is included in package."""
        packaged = get_packaged_modules()
        assert 'handler' in packaged, "handler.py not in Lambda package"

    @pytest.mark.parametrize("module_name,source_path", [
        pytest.param(name, path, id=name)
        for name, path in get_packaged_modules().items()
    ])
    def test_module_imports_are_available(self, module_name, source_path):
        """Verify all imports used by this module are available."""
        packaged = set(get_packaged_modules().keys())
        missing = get_missing_imports(source_path, packaged)
        assert not missing, f"{module_name}.py imports missing modules: {missing}"

    @pytest.mark.parametrize("module_name,source_path", [
        pytest.param(name, path, id=name)
        for name, path in get_packaged_modules().items()
    ])
    def test_source_file_exists(self, module_name, source_path):
        """Verify source file referenced in data.tf exists."""
        assert source_path.exists(), f"{module_name}: {source_path} not found"
