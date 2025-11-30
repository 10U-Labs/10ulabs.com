from test.health.conftest import HEALTH_SRC, REPO_ROOT

LAMBDA_FILE = HEALTH_SRC / "lambda.tf"
API_SRC = REPO_ROOT / "src" / "api"


def test_lambda_terraform_file_exists():
    assert LAMBDA_FILE.exists()


def test_health_handler_archive_file_exists():
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "health_handler"' in content


def test_health_handler_lambda_function_exists():
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "health_handler"' in content


def test_health_handler_cloudwatch_log_group_exists():
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_group" "health_handler"' in content


def test_health_handler_log_subscription_exists():
    log_subs_file = API_SRC / "log_subscriptions.tf"
    with open(log_subs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "health_handler"' in content


def test_health_handler_api_gateway_permission_exists():
    apigateway_file = API_SRC / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_permission" "health_handler"' in content


def test_health_handler_uses_python_313_runtime():
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'runtime          = "python3.13"' in content


def test_health_handler_has_timeout():
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'timeout          = 10' in content


def test_health_handler_has_description():
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'description      = "Health check endpoint for API"' in content


def test_health_handler_source_file_path():
    with open(LAMBDA_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'source_file = "${path.module}/lambda/handler.py"' in content


def test_health_handler_py_file_exists():
    handler_file = HEALTH_SRC / "lambda" / "handler.py"
    assert handler_file.exists()
