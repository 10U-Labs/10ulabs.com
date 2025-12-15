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


def test_scanner_lambda_function_exists():
    """Verify scanner Lambda function resource is defined."""
    lambda_file = AGENTS_SRC / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "scanner"' in content


def test_invoker_lambda_function_exists():
    """Verify invoker Lambda function resource is defined."""
    lambda_file = AGENTS_SRC / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "invoker"' in content


def test_webhook_lambda_archive_exists():
    """Verify webhook archive_file data source is defined."""
    lambda_file = AGENTS_SRC / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "webhook_lambda"' in content


def test_scanner_lambda_archive_exists():
    """Verify scanner archive_file data source is defined."""
    lambda_file = AGENTS_SRC / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "scanner_lambda"' in content


def test_invoker_lambda_archive_exists():
    """Verify invoker archive_file data source is defined."""
    lambda_file = AGENTS_SRC / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "invoker_lambda"' in content


def test_webhook_sqs_event_source_mapping_exists():
    """Verify webhook SQS event source mapping is defined."""
    lambda_file = AGENTS_SRC / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_event_source_mapping" "webhook_sqs"' in content


def test_scanner_sqs_event_source_mapping_exists():
    """Verify scanner SQS event source mapping is defined."""
    lambda_file = AGENTS_SRC / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_event_source_mapping" "scanner_sqs"' in content


def test_invoker_sqs_event_source_mapping_exists():
    """Verify invoker SQS event source mapping is defined."""
    lambda_file = AGENTS_SRC / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_event_source_mapping" "invoker_sqs"' in content
