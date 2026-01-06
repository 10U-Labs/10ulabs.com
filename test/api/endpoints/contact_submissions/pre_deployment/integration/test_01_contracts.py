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


def test_lambda_handler_function_exists():
    """Verify Lambda handler.py exports a handler function."""
    handler_path = LAMBDA_DIR / "handler.py"
    content = handler_path.read_text()
    has_handler = "def handler(" in content
    assert has_handler, (
        "handler.py must export a 'handler' function. "
        "Terraform expects handler.handler as the entry point."
    )


def test_terraform_handler_matches_lambda_export():
    """Verify Terraform handler config matches Lambda export."""
    lambda_tf_path = ENDPOINT_SRC / "lambda.tf"
    content = lambda_tf_path.read_text()

    # Extract handler value from Terraform
    match = re.search(r'handler\s*=\s*"([^"]+)"', content)
    terraform_handler = match.group(1) if match else None
    assert terraform_handler is not None, "Could not find handler in lambda.tf"

    # Parse file.function format
    parts = terraform_handler.split(".")
    handler_has_two_parts = len(parts) == 2
    assert handler_has_two_parts, (
        f"Handler '{terraform_handler}' should be in format 'file.function'"
    )

    handler_file, handler_function = parts

    # Verify the file exists
    handler_py_path = LAMBDA_DIR / f"{handler_file}.py"
    handler_file_exists = handler_py_path.exists()
    assert handler_file_exists, (
        f"Terraform references {handler_file}.py but file does not exist at "
        f"{handler_py_path}"
    )

    # Verify the function exists in the file
    handler_content = handler_py_path.read_text()
    function_pattern = rf"def {handler_function}\s*\("
    function_exists = re.search(function_pattern, handler_content) is not None
    assert function_exists, (
        f"Terraform expects function '{handler_function}' in {handler_file}.py "
        f"but it was not found"
    )


def test_lambda_directory_exists():
    """Verify Lambda source directory exists."""
    lambda_dir_exists = LAMBDA_DIR.exists()
    assert lambda_dir_exists, f"Lambda directory not found at {LAMBDA_DIR}"


def test_terraform_files_exist():
    """Verify required Terraform files exist."""
    required_files = ["lambda.tf", "iam.tf", "variables.tf"]
    for tf_file in required_files:
        tf_path = ENDPOINT_SRC / tf_file
        file_exists = tf_path.exists()
        assert file_exists, f"Required Terraform file not found: {tf_path}"
