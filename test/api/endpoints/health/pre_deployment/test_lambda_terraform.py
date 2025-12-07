"""Unit tests for health endpoint Lambda Terraform configuration."""
from test.api.endpoints.health.conftest import HEALTH_SRC, REPO_ROOT

LAMBDA_FILE = HEALTH_SRC / "lambda.tf"
API_BACKEND_SRC = REPO_ROOT / "src" / "api" / "backend"


def test_lambda_terraform_file_exists():
    """Verify lambda.tf file exists."""
    assert LAMBDA_FILE.exists()


def test_health_handler_archive_file_exists():
    """Verify archive_file data source is defined."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "health_handler"' in content


def test_health_handler_lambda_function_exists():
    """Verify Lambda function resource is defined."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "health_handler"' in content


def test_health_handler_cloudwatch_log_group_exists():
    """Verify CloudWatch log group is defined."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_group" "health_handler"' in content


def test_health_handler_log_subscription_exists():
    """Verify log subscription filter is defined."""
    log_subs_file = API_BACKEND_SRC / "log_subscriptions.tf"
    with open(log_subs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "health_handler"' in content


def test_health_handler_api_gateway_permission_exists():
    """Verify API Gateway Lambda permission is defined in the health stack."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_permission" "api_gateway"' in content


def test_health_handler_uses_python_313_runtime():
    """Verify Python 3.13 runtime is used."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'runtime          = "python3.13"' in content


def test_health_handler_has_timeout():
    """Verify Lambda timeout is set."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'timeout          = 10' in content


def test_health_handler_has_description():
    """Verify Lambda description is set."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'description      = "Health check endpoint for API"' in content


def test_health_handler_source_file_path():
    """Verify correct source file path."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'source_file = "${path.module}/lambda/handler.py"' in content


def test_health_handler_py_file_exists():
    """Verify handler.py file exists."""
    handler_file = HEALTH_SRC / "lambda" / "handler.py"
    assert handler_file.exists()
