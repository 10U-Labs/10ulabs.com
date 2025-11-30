from pathlib import Path


def test_apigateway_terraform_file_exists():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    assert apigateway_file.exists()


def test_api_gateway_cloudwatch_log_group_exists():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_group" "api_gateway"' in content


def test_api_gateway_rest_api_exists():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_api_gateway_rest_api" "main"' in content


def test_api_gateway_rest_api_name_uses_variable():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'var.api_gateway_name' in content


def test_api_gateway_deployment_exists():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_api_gateway_deployment" "main"' in content


def test_api_gateway_stage_exists():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_api_gateway_stage" "prod"' in content


def test_api_gateway_stage_has_access_logging():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'access_log_settings' in content


def test_api_gateway_stage_has_xray_tracing():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'xray_tracing_enabled' in content


def test_lambda_permission_health_handler_exists():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_permission" "health_handler"' in content


def test_lambda_permission_v1_handler_exists():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_permission" "v1_handler"' in content


def test_lambda_permission_runners_handler_exists():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_permission" "runners_handler"' in content


def test_lambda_permission_catchall_handler_exists():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_permission" "catchall_handler"' in content


def test_api_key_random_password_exists():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "random_password" "api_key"' in content


def test_api_gateway_api_key_exists():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_api_gateway_api_key" "main"' in content


def test_api_gateway_usage_plan_exists():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_api_gateway_usage_plan" "main"' in content


def test_api_gateway_usage_plan_key_exists():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_api_gateway_usage_plan_key" "main"' in content


def test_api_gateway_propagation_wait_resource_exists():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "null_resource" "api_gateway_propagation_wait"' in content


def test_api_gateway_propagation_wait_depends_on_stage():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert "aws_api_gateway_stage.prod" in content


def test_api_gateway_propagation_wait_depends_on_echo_permission():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert "aws_lambda_permission.echo_handler" in content


def test_api_gateway_propagation_wait_triggers_on_deployment():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert "aws_api_gateway_deployment.main.id" in content


def test_api_gateway_propagation_wait_uses_exponential_backoff():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert "1 << N" in content


def test_api_gateway_propagation_wait_polls_echo_endpoint():
    apigateway_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "apigateway.tf"
    with open(apigateway_file, encoding="utf-8") as f:
        content = f.read()
    assert "/v1/echo" in content
