import re
from pathlib import Path
from typing import Any, Dict

from repo_utils import REPO_ROOT as _REPO_ROOT, extract_brace_block

COMMON_MODULE_DIR = _REPO_ROOT / "lib" / "terraform" / "common"


def _parse_map_block(content: str, map_name: str) -> Dict[str, str]:
    pattern = rf'{map_name}\s*=\s*\{{'
    match = re.search(pattern, content)
    if not match:
        return {}

    block_content = extract_brace_block(content, match.end() - 1)
    values = {}
    entry_pattern = r'(\w+)\s*=\s*"([^"]+)"'
    for entry_match in re.finditer(entry_pattern, block_content):
        key, value = entry_match.groups()
        values[key] = value
    return values


def _parse_locals() -> Dict[str, str]:
    locals_path = COMMON_MODULE_DIR / "locals.tf"
    with open(locals_path, encoding="utf-8") as f:
        content = f.read()

    values = {}
    pattern = r'(\w+)\s*=\s*"([^"]+)"'
    for match in re.finditer(pattern, content):
        key, value = match.groups()
        values[key] = value
    return values


def parse_lambda_handler_names() -> Dict[str, str]:
    locals_path = COMMON_MODULE_DIR / "locals.tf"
    with open(locals_path, encoding="utf-8") as f:
        content = f.read()

    raw_values = _parse_map_block(content, "lambda_handler_names")

    locals_dict = _parse_locals()
    resource_prefix = locals_dict.get("resource_prefix", "")

    resolved = {}
    for key, value in raw_values.items():
        resolved[key] = value.replace("${local.resource_prefix}", resource_prefix)
    return resolved


def _parse_outputs() -> Dict[str, str]:
    outputs_path = COMMON_MODULE_DIR / "outputs.tf"
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()

    locals_dict = _parse_locals()
    values = {}

    literal_pattern = r'output\s+"([^"]+)"\s*\{\s*value\s*=\s*"([^"]+)"'
    for match in re.findall(literal_pattern, content):
        output_name, value = match
        values[output_name] = value

    local_pattern = r'output\s+"([^"]+)"\s*\{\s*value\s*=\s*local\.(\w+)'
    for match in re.findall(local_pattern, content):
        output_name, local_name = match
        if local_name in locals_dict:
            values[output_name] = locals_dict[local_name]

    return values


def get_shared_config() -> Dict[str, Any]:
    config: Dict[str, Any] = _parse_locals()
    config.update(_parse_outputs())
    config["lambda_handler_names"] = parse_lambda_handler_names()
    domain_name = config.get("domain_name", "")
    if domain_name:
        config["api_fqdn"] = f"api.{domain_name}"
    return config


TEST_AWS_REGION = _parse_locals().get("aws_region", "us-east-2")


def get_resource_prefix() -> str:
    return _parse_locals().get("resource_prefix", "TenULabs")


def _resolve_local_interpolations(value: str, local_values: Dict[str, str]) -> str:
    max_iterations = 10
    for _ in range(max_iterations):
        new_value = value
        for local_name, local_value in local_values.items():
            new_value = new_value.replace(f"${{local.{local_name}}}", local_value)
        if new_value == value:
            break
        value = new_value
    return value


def packaged_lambda_sources(tf_file: Path) -> list:
    pattern = r'(?:source_file\s*=|content\s*=\s*file\()\s*"\$\{path\.module\}/([^"]+)"'
    content = tf_file.read_text(encoding="utf-8")
    return [
        packaged
        for packaged in re.findall(pattern, content)
        if packaged.endswith(".py") and ".." not in Path(packaged).parts
    ]


def packaged_lambda_archives(tf_file: Path) -> list:
    pattern = r'output_path\s*=\s*"\$\{path\.module\}/([^"]+)"'
    content = tf_file.read_text(encoding="utf-8")
    return re.findall(pattern, content)
