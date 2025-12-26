"""Tests for lambda.tf Terraform configuration."""

from pathlib import Path


def _get_terraform_path() -> Path:
    """Get the path to lambda.tf file."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent
    return base / "src" / "api" / "backend" / "lambda.tf"


def test_lambda_terraform_file_exists():
    """Verify that lambda.tf file exists."""
    lambda_file = _get_terraform_path()
    file_exists = lambda_file.exists()
    assert file_exists


def test_catchall_handler_archive_file_exists():
    """Verify that catchall handler archive file resource exists."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    contains_archive_file = 'data "archive_file" "catchall_handler"' in content
    assert contains_archive_file


def test_catchall_handler_lambda_function_exists():
    """Verify that catchall handler Lambda function resource exists."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    contains_lambda_function = 'resource "aws_lambda_function" "catchall_handler"' in content
    assert contains_lambda_function


def test_catchall_handler_cloudwatch_log_group_exists():
    """Verify that catchall handler CloudWatch log group resource exists."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    contains_log_group = 'resource "aws_cloudwatch_log_group" "catchall_handler"' in content
    assert contains_log_group
