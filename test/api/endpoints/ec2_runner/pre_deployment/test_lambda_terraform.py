"""Unit tests for EC2 runner Lambda Terraform configuration."""
from test.api.endpoints.conftest import assert_archive_includes_file

from ..conftest import EC2_RUNNER_SRC


def test_lambda_terraform_file_exists():
    """Verify lambda.tf file exists."""
    lambda_file = EC2_RUNNER_SRC / "lambda.tf"
    assert lambda_file.exists()


def test_handler_archive_file_exists():
    """Verify archive_file data source is defined."""
    lambda_file = EC2_RUNNER_SRC / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "handler"' in content


def test_handler_lambda_function_exists():
    """Verify Lambda function resource is defined."""
    lambda_file = EC2_RUNNER_SRC / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "handler"' in content


def test_handler_archive_includes_runner_labels():
    """Test handler archive includes runner_labels.py shared module.

    This is a regression test to ensure the Lambda package includes the
    runner_labels module. Without this module, the Lambda will fail at runtime
    with a ModuleNotFoundError when parsing job labels.
    """
    lambda_file = EC2_RUNNER_SRC / "lambda.tf"
    assert_archive_includes_file(lambda_file, "handler", "runner_labels.py")
