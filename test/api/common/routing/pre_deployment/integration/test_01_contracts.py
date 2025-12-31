"""Layer 1: Contract tests for api_common_routing pre-deployment validation.

Verify that the contract between openapi.json template variables and
apigateway.tf templatefile() parameters is satisfied.
"""
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.layer(1)


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
