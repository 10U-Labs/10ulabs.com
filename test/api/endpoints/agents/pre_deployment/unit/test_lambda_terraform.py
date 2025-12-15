"""Unit tests for agents Lambda Terraform configuration."""
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


def test_lambda_terraform_file_exists():
    """Verify lambda.tf file exists."""
    lambda_file = AGENTS_SRC / "lambda.tf"
    assert lambda_file.exists()


def test_webhook_lambda_function_exists():
    """Verify webhook Lambda function resource is defined."""
    lambda_file = AGENTS_SRC / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "webhook"' in content


def test_lambda_function_url_resource_exists():
    """Verify Lambda function URL resource is defined."""
    lambda_file = AGENTS_SRC / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function_url" "webhook"' in content


def test_eventbridge_rule_resource_exists():
    """Verify EventBridge scheduled rule resource is defined."""
    lambda_file = AGENTS_SRC / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_event_rule"' in content


def test_webhook_lambda_handler_archive_exists():
    """Verify handler archive_file data source is defined."""
    lambda_file = AGENTS_SRC / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file"' in content
