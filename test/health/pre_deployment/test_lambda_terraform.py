from pathlib import Path


def test_lambda_terraform_file_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "lambda.tf"
    assert lambda_file.exists()


def test_health_handler_archive_file_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "health_handler"' in content


def test_health_handler_lambda_function_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "health_handler"' in content


def test_health_handler_cloudwatch_log_group_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_group" "health_handler"' in content


def test_health_handler_log_subscription_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "health_handler"' in content


def test_health_handler_api_gateway_permission_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_permission" "health_handler"' in content


def test_health_handler_uses_python_313_runtime():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'runtime          = "python3.13"' in content


def test_health_handler_has_timeout():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'timeout          = 10' in content


def test_health_handler_has_description():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'description      = "Health check endpoint for API"' in content
