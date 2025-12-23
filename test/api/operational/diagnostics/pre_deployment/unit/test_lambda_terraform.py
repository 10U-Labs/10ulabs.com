"""Unit tests for diagnostics endpoint Lambda Terraform configuration."""
from test.api.operational.diagnostics.pre_deployment.unit.conftest import DIAGNOSTICS_SRC

LAMBDA_FILE = DIAGNOSTICS_SRC / "lambda.tf"


def test_lambda_terraform_file_exists():
    """Verify lambda.tf file exists."""
    assert LAMBDA_FILE.exists()


def test_diagnostics_handler_archive_file_exists():
    """Verify archive_file data source is defined."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "diagnostics_handler"' in content


def test_diagnostics_handler_lambda_function_exists():
    """Verify Lambda function resource is defined."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "diagnostics_handler"' in content


def test_diagnostics_handler_cloudwatch_log_group_exists():
    """Verify CloudWatch log group is defined."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_group" "diagnostics_handler"' in content


def test_diagnostics_handler_api_gateway_permission_exists():
    """Verify API Gateway Lambda permission is defined."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_permission" "api_gateway"' in content


def test_diagnostics_handler_uses_python_313_runtime():
    """Verify Python 3.13 runtime is used."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'runtime          = "python3.13"' in content


def test_diagnostics_handler_has_timeout():
    """Verify Lambda timeout is set."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'timeout          = 10' in content


def test_diagnostics_handler_has_description():
    """Verify Lambda description is set."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'description      = "Diagnostics endpoint for API"' in content


def test_diagnostics_handler_source_file_path():
    """Verify correct source file path."""
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'source_file = "${path.module}/lambda/handler.py"' in content


def test_diagnostics_handler_py_file_exists():
    """Verify handler.py file exists."""
    handler_file = DIAGNOSTICS_SRC / "lambda" / "handler.py"
    assert handler_file.exists()
