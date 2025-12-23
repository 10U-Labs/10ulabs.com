"""Unit tests for diagnostics endpoint outputs Terraform configuration."""
from test.api.operational.diagnostics.pre_deployment.unit.conftest import DIAGNOSTICS_SRC

OUTPUTS_FILE = DIAGNOSTICS_SRC / "outputs.tf"


def test_outputs_terraform_file_exists():
    """Verify outputs.tf file exists."""
    assert OUTPUTS_FILE.exists()


def test_lambda_function_arn_output_exists():
    """Verify lambda_function_arn output is defined."""
    with open(OUTPUTS_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'output "lambda_function_arn"' in content


def test_lambda_function_name_output_exists():
    """Verify lambda_function_name output is defined."""
    with open(OUTPUTS_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'output "lambda_function_name"' in content


def test_log_group_name_output_exists():
    """Verify log_group_name output is defined."""
    with open(OUTPUTS_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'output "log_group_name"' in content
