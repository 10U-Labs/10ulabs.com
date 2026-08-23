"""Layer 1: Contract tests for api_common_routing pre-deployment validation.

Verify that the contract between openapi.json template variables and
apigateway.tf templatefile() parameters is satisfied, and that the shared
setup these tests are built from still describes things that exist.
"""
import re
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT
from test.api.common.routing.conftest import _add_derived_config

ROUTING_SRC = REPO_ROOT / "src" / "api" / "common" / "routing"
LAMBDAS_DIR = ROUTING_SRC / "lambdas"
UNIT_CONFTEST = (
    REPO_ROOT / "test" / "api" / "common" / "routing"
    / "pre_deployment" / "unit" / "conftest.py"
)
_DERIVED_NAME_PREFIX = "SentinelResourcePrefix"


def _extract_openapi_template_vars(openapi_path: Path) -> set[str]:
    """Extract all ${VarName} template variables from openapi.json."""
    content = openapi_path.read_text()
    # Match ${VarName} pattern - Terraform templatefile syntax
    pattern = r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}"
    return set(re.findall(pattern, content))


def _extract_templatefile_vars(apigateway_path: Path) -> set[str]:
    """Extract variables passed to templatefile() in apigateway.tf."""
    content = apigateway_path.read_text()

    # Find the templatefile block - it starts with "templatefile(" and ends with "})"
    # The variables are in a block like: templatefile("...", { VarName = value, ... })
    match = re.search(
        r"templatefile\s*\(\s*\"[^\"]+\"\s*,\s*\{([^}]+)\}\s*\)",
        content,
        re.DOTALL,
    )
    if not match:
        return set()

    vars_block = match.group(1)
    # Extract variable names (left side of = in key = value pairs)
    var_pattern = r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*="
    return set(re.findall(var_pattern, vars_block, re.MULTILINE))


def test_openapi_json_exists(openapi_path: Path):
    """Verify openapi.json file exists."""
    assert openapi_path.exists(), f"openapi.json not found at {openapi_path}"


def test_apigateway_tf_exists(apigateway_path: Path):
    """Verify apigateway.tf file exists."""
    assert apigateway_path.exists(), f"apigateway.tf not found at {apigateway_path}"


def test_openapi_template_vars_all_provided(openapi_path: Path, apigateway_path: Path):
    """Verify all template variables in openapi.json are passed to templatefile."""
    if not openapi_path.exists() or not apigateway_path.exists():
        pytest.skip("Required files do not exist")

    openapi_vars = _extract_openapi_template_vars(openapi_path)
    templatefile_vars = _extract_templatefile_vars(apigateway_path)

    missing_vars = openapi_vars - templatefile_vars
    assert not missing_vars, (
        f"Template variables in openapi.json are missing from templatefile() call:\n"
        f"  Missing: {sorted(missing_vars)}\n"
        f"  openapi.json requires: {sorted(openapi_vars)}\n"
        f"  apigateway.tf provides: {sorted(templatefile_vars)}"
    )


def test_templatefile_vars_all_used(openapi_path: Path, apigateway_path: Path):
    """Verify all templatefile() variables are actually used in openapi.json."""
    if not openapi_path.exists() or not apigateway_path.exists():
        pytest.skip("Required files do not exist")

    openapi_vars = _extract_openapi_template_vars(openapi_path)
    templatefile_vars = _extract_templatefile_vars(apigateway_path)

    unused_vars = templatefile_vars - openapi_vars
    assert not unused_vars, (
        f"Variables passed to templatefile() are not used in openapi.json:\n"
        f"  Unused: {sorted(unused_vars)}\n"
        f"  apigateway.tf provides: {sorted(templatefile_vars)}\n"
        f"  openapi.json uses: {sorted(openapi_vars)}"
    )


# =============================================================================
# Lambda Handler Contract Tests
# =============================================================================


def _extract_lambda_handlers_from_tf(lambda_tf_path: Path) -> list[tuple[str, str]]:
    """Extract Lambda handler references from lambda.tf.

    Returns list of (resource_name, handler_ref) tuples.
    handler_ref format: "filename.function_name"
    """
    content = lambda_tf_path.read_text()
    handlers = []

    # Match resource "aws_lambda_function" "name" blocks and their handler attribute
    resource_pattern = r'resource\s+"aws_lambda_function"\s+"(\w+)"'
    handler_pattern = r'handler\s*=\s*"([^"]+)"'

    # Find all lambda function resources
    for resource_match in re.finditer(resource_pattern, content):
        resource_name = resource_match.group(1)
        # Find the handler in the block following this resource
        start = resource_match.end()
        # Find next resource or end of file to limit search scope
        next_resource = re.search(r'\nresource\s+', content[start:])
        end = start + next_resource.start() if next_resource else len(content)
        block_content = content[start:end]

        handler_match = re.search(handler_pattern, block_content)
        if handler_match:
            handler_ref = handler_match.group(1)
            handlers.append((resource_name, handler_ref))

    return handlers


def _extract_function_names_from_py(py_path: Path) -> set[str]:
    """Extract top-level function names from Python file."""
    content = py_path.read_text()
    # Match def function_name( at start of line (no indentation)
    pattern = r'^def\s+(\w+)\s*\('
    return set(re.findall(pattern, content, re.MULTILINE))


def test_lambda_handler_exports_match_terraform_references(
    lambda_tf_path: Path, lambdas_dir: Path
):
    """Verify Lambda handler exports match Terraform handler references.

    Terraform handler = "catchall.handler" means:
    - File: lambdas/catchall.py
    - Function: handler()

    This test verifies that each handler reference in lambda.tf
    corresponds to an actual function export in the Python file.
    """
    if not lambda_tf_path.exists():
        pytest.skip("lambda.tf not found")

    handlers = _extract_lambda_handlers_from_tf(lambda_tf_path)
    if not handlers:
        pytest.skip("No Lambda handler references found in lambda.tf")

    errors = []
    for resource_name, handler_ref in handlers:
        # Parse handler reference (format: filename.function_name)
        parts = handler_ref.split(".")
        if len(parts) != 2:
            errors.append(
                f"  {resource_name}: Invalid handler format '{handler_ref}' "
                f"(expected 'filename.function_name')"
            )
            continue

        expected_module, expected_function = parts
        py_file = lambdas_dir / f"{expected_module}.py"

        if not py_file.exists():
            errors.append(
                f"  {resource_name}: Handler references '{expected_module}.py' "
                f"but file does not exist at {py_file}"
            )
            continue

        functions = _extract_function_names_from_py(py_file)
        if expected_function not in functions:
            errors.append(
                f"  {resource_name}: Handler references function '{expected_function}' "
                f"but {expected_module}.py only exports: {sorted(functions)}"
            )

    assert not errors, (
        "Lambda handler contracts violated:\n" + "\n".join(errors)
    )


# =============================================================================
# Shared Setup Contract Tests
# =============================================================================


def _lambda_sources_the_unit_setup_opens() -> list[str]:
    """Read the unit tier's setup as text and list the Lambda files it opens.

    The setup opens each file from inside a fixture, and a fixture no test
    requests never runs, so the filenames are only reachable as text.
    """
    content = UNIT_CONFTEST.read_text()
    return sorted(set(re.findall(r'load_lambda_module\(\s*"([^"]+)"', content)))


@pytest.mark.parametrize("lambda_source", _lambda_sources_the_unit_setup_opens())
def test_unit_setup_opens_a_lambda_source_that_exists(lambda_source: str):
    """Verify every Lambda source the unit tier's setup opens is on disk."""
    assert (LAMBDAS_DIR / lambda_source).exists(), (
        f"The unit tier's setup opens '{lambda_source}', which is not in "
        f"{LAMBDAS_DIR}. A test requesting that fixture dies with "
        f"FileNotFoundError."
    )


def _derived_resource_names() -> list[str]:
    """Ask the shared setup for the names it derives, prefix stripped.

    The setup writes each name whole while the Terraform builds it by joining
    a prefix to a suffix, so a sentinel prefix goes in and comes back off.
    """
    derived: dict[str, str] = {"resource_prefix": _DERIVED_NAME_PREFIX}
    _add_derived_config(derived)
    return sorted(
        value.removeprefix(_DERIVED_NAME_PREFIX)
        for key, value in derived.items()
        if key != "resource_prefix"
    )


@pytest.mark.parametrize("derived_name", _derived_resource_names())
def test_derived_resource_name_is_built_by_this_terraform(derived_name: str):
    """Verify every name the shared setup derives is one this Terraform builds."""
    terraform = "\n".join(path.read_text() for path in sorted(ROUTING_SRC.glob("*.tf")))
    assert derived_name in terraform, (
        f"The shared setup derives a name ending '{derived_name}', which no "
        f"Terraform file in {ROUTING_SRC} builds. Whatever owned it has left."
    )
