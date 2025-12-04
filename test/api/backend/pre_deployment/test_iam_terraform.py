"""Tests for iam.tf Terraform configuration."""

from pathlib import Path


def _get_terraform_path() -> Path:
    """Get the path to iam.tf file."""
    base = Path(__file__).parent.parent.parent.parent.parent
    return base / "src" / "api" / "backend" / "iam.tf"


def test_iam_terraform_file_exists():
    """Verify that iam.tf file exists."""
    iam_file = _get_terraform_path()
    file_exists = iam_file.exists()
    assert file_exists


def test_lambda_catchall_handler_role_exists():
    """Verify that Lambda catchall handler IAM role exists."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    role_exists = 'resource "aws_iam_role" "lambda_catchall_handler"' in content
    assert role_exists
