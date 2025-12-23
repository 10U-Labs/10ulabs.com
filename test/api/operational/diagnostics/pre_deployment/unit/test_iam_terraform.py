"""Unit tests for diagnostics endpoint IAM Terraform configuration."""
from test.api.operational.diagnostics.pre_deployment.unit.conftest import DIAGNOSTICS_SRC

IAM_FILE = DIAGNOSTICS_SRC / "iam.tf"


def test_iam_terraform_file_exists():
    """Verify iam.tf file exists."""
    assert IAM_FILE.exists()


def test_diagnostics_handler_iam_role_exists():
    """Verify IAM role resource is defined."""
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "lambda_diagnostics_handler"' in content


def test_diagnostics_handler_iam_role_has_lambda_assume_role():
    """Verify IAM role allows Lambda assume role."""
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'lambda.amazonaws.com' in content


def test_diagnostics_handler_has_basic_execution_role_attachment():
    """Verify basic execution role attachment exists."""
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy_attachment" "lambda_diagnostics_handler_basic"' in content


def test_diagnostics_handler_uses_basic_execution_policy():
    """Verify basic execution policy is used."""
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'AWSLambdaBasicExecutionRole' in content
