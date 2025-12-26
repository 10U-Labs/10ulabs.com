"""Layer 1: Contract tests for api_shared_routing pre-deployment validation.

Verify that local files that must work together are compatible.
These tests run before AWS authentication checks.
"""
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.layer(1)

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
ROUTING_DIR = REPO_ROOT / "src" / "api" / "shared" / "routing"
OPENAPI_PATH = REPO_ROOT / "src" / "www" / "api" / "openapi.json"


def _read_openapi_json() -> str:
    """Read the OpenAPI spec file."""
    return OPENAPI_PATH.read_text(encoding="utf-8")


def _read_apigateway_tf() -> str:
    """Read the apigateway.tf file."""
    return (ROUTING_DIR / "apigateway.tf").read_text(encoding="utf-8")


def _extract_templatefile_block(tf_content: str) -> str:
    """Extract the templatefile() block from apigateway.tf."""
    # Find the templatefile call and extract the vars block
    match = re.search(
        r'openapi_spec\s*=\s*templatefile\([^,]+,\s*\{([^}]+)\}\)',
        tf_content,
        re.DOTALL
    )
    return match.group(1) if match else ""


def test_openapi_template_vars_all_provided():
    """Verify all template variables in openapi.json are passed to templatefile."""
    openapi_content = _read_openapi_json()
    tf_content = _read_apigateway_tf()

    # Extract ${VarName} from openapi.json
    template_vars = set(re.findall(r'\$\{(\w+)\}', openapi_content))

    # Extract variables passed to templatefile in apigateway.tf
    templatefile_block = _extract_templatefile_block(tf_content)
    provided_vars = set(re.findall(r'^\s*(\w+)\s*=', templatefile_block, re.MULTILINE))

    missing = template_vars - provided_vars
    assert not missing, (
        f"Template variables in openapi.json missing from templatefile(): {missing}\n"
        f"Add these to the templatefile() call in apigateway.tf"
    )


def test_templatefile_vars_all_used():
    """Verify all templatefile vars are actually used in openapi.json."""
    openapi_content = _read_openapi_json()
    tf_content = _read_apigateway_tf()

    # Extract ${VarName} from openapi.json
    template_vars = set(re.findall(r'\$\{(\w+)\}', openapi_content))

    # Extract variables passed to templatefile in apigateway.tf
    templatefile_block = _extract_templatefile_block(tf_content)
    provided_vars = set(re.findall(r'^\s*(\w+)\s*=', templatefile_block, re.MULTILINE))

    unused = provided_vars - template_vars
    assert not unused, (
        f"Variables passed to templatefile() but not used in openapi.json: {unused}\n"
        f"Remove these from the templatefile() call in apigateway.tf"
    )
