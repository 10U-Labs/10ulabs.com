"""Layer 1: Contract tests for contact_submissions.

These tests verify local file compatibility without making AWS calls.
They catch contract mismatches between files before deployment.
"""
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.layer(1)

# Path from test file to repo root:
# test/api/endpoints/contact_submissions/pre_deployment/integration/test_01_contracts.py
# (7 parent directories to get to repo root)
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
ENDPOINT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "contact_submissions"
LAMBDA_DIR = ENDPOINT_SRC / "lambda"


def _get_terraform_handler():
    """Extract handler value from lambda.tf."""
    lambda_tf_path = ENDPOINT_SRC / "lambda.tf"
    content = lambda_tf_path.read_text()
    match = re.search(r'handler\s*=\s*"([^"]+)"', content)
    return match.group(1) if match else None


def test_lambda_handler_function_exists():
    """Verify Lambda handler.py exports a handler function."""
    handler_path = LAMBDA_DIR / "handler.py"
    content = handler_path.read_text()
    has_handler = "def handler(" in content
    assert has_handler


def test_terraform_lambda_tf_has_handler_config():
    """Verify lambda.tf has a handler configuration."""
    terraform_handler = _get_terraform_handler()
    handler_is_configured = terraform_handler is not None
    assert handler_is_configured


def test_terraform_handler_has_correct_format():
    """Verify Terraform handler is in file.function format."""
    terraform_handler = _get_terraform_handler()
    parts = terraform_handler.split(".") if terraform_handler else []
    handler_has_two_parts = len(parts) == 2
    assert handler_has_two_parts


def test_terraform_handler_file_exists():
    """Verify the file referenced by Terraform handler exists."""
    terraform_handler = _get_terraform_handler()
    parts = terraform_handler.split(".") if terraform_handler else []
    handler_file = parts[0] if len(parts) == 2 else None
    handler_py_path = LAMBDA_DIR / f"{handler_file}.py" if handler_file else None
    handler_file_exists = handler_py_path.exists() if handler_py_path else False
    assert handler_file_exists


def test_terraform_handler_function_exists_in_file():
    """Verify the function referenced by Terraform handler exists."""
    terraform_handler = _get_terraform_handler()
    parts = terraform_handler.split(".") if terraform_handler else []
    if len(parts) != 2:
        pytest.skip("Handler format invalid")
    handler_file, handler_function = parts
    handler_py_path = LAMBDA_DIR / f"{handler_file}.py"
    handler_content = handler_py_path.read_text()
    function_pattern = rf"def {handler_function}\s*\("
    function_exists = re.search(function_pattern, handler_content) is not None
    assert function_exists


def test_lambda_directory_exists():
    """Verify Lambda source directory exists."""
    lambda_dir_exists = LAMBDA_DIR.exists()
    assert lambda_dir_exists


@pytest.mark.parametrize("tf_file", ["lambda.tf", "iam.tf", "variables.tf"])
def test_terraform_file_exists(tf_file):
    """Verify required Terraform file exists."""
    tf_path = ENDPOINT_SRC / tf_file
    file_exists = tf_path.exists()
    assert file_exists
