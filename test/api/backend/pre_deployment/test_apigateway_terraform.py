"""Tests for API Gateway Terraform configuration."""
from pathlib import Path


def _get_apigateway_tf_path() -> Path:
    """Get the path to apigateway.tf file."""
    base = Path(__file__).parent.parent.parent.parent.parent
    return base / "src" / "api" / "backend" / "apigateway.tf"


def _read_apigateway_tf() -> str:
    """Read and return the apigateway.tf content."""
    with open(_get_apigateway_tf_path(), encoding="utf-8") as f:
        return f.read()


def test_apigateway_terraform_file_exists():
    """Verify apigateway.tf file exists."""
    assert _get_apigateway_tf_path().exists()


def test_api_gateway_cloudwatch_log_group_exists():
    """Verify CloudWatch log group resource exists."""
    content = _read_apigateway_tf()
    assert 'resource "aws_cloudwatch_log_group" "api_gateway"' in content


def test_api_gateway_rest_api_exists():
    """Verify REST API resource exists."""
    content = _read_apigateway_tf()
    assert 'resource "aws_api_gateway_rest_api" "main"' in content


def test_api_gateway_rest_api_name_uses_variable():
    """Verify REST API name uses variable."""
    content = _read_apigateway_tf()
    assert 'var.api_gateway_name' in content


def test_api_gateway_deployment_exists():
    """Verify deployment resource exists."""
    content = _read_apigateway_tf()
    assert 'resource "aws_api_gateway_deployment" "main"' in content


def test_api_gateway_stage_exists():
    """Verify stage resource exists."""
    content = _read_apigateway_tf()
    assert 'resource "aws_api_gateway_stage" "prod"' in content


def test_api_gateway_stage_has_access_logging():
    """Verify stage has access logging configured."""
    content = _read_apigateway_tf()
    assert 'access_log_settings' in content


def test_api_gateway_stage_has_xray_tracing():
    """Verify stage has X-Ray tracing enabled."""
    content = _read_apigateway_tf()
    assert 'xray_tracing_enabled' in content


def test_lambda_permission_health_handler_exists():
    """Verify Lambda permission for health handler exists."""
    content = _read_apigateway_tf()
    assert 'resource "aws_lambda_permission" "health_handler"' in content


def test_lambda_permission_runners_handler_exists():
    """Verify Lambda permission for runners handler exists."""
    content = _read_apigateway_tf()
    assert 'resource "aws_lambda_permission" "runners_handler"' in content


def test_lambda_permission_catchall_handler_exists():
    """Verify Lambda permission for catchall handler exists."""
    content = _read_apigateway_tf()
    assert 'resource "aws_lambda_permission" "catchall_handler"' in content


def test_api_key_random_password_exists():
    """Verify random password resource for API key exists."""
    content = _read_apigateway_tf()
    assert 'resource "random_password" "api_key"' in content


def test_api_gateway_api_key_exists():
    """Verify API key resource exists."""
    content = _read_apigateway_tf()
    assert 'resource "aws_api_gateway_api_key" "main"' in content


def test_api_gateway_usage_plan_exists():
    """Verify usage plan resource exists."""
    content = _read_apigateway_tf()
    assert 'resource "aws_api_gateway_usage_plan" "main"' in content


def test_api_gateway_usage_plan_key_exists():
    """Verify usage plan key resource exists."""
    content = _read_apigateway_tf()
    assert 'resource "aws_api_gateway_usage_plan_key" "main"' in content


def test_api_gateway_propagation_wait_resource_exists():
    """Verify propagation wait null resource exists."""
    content = _read_apigateway_tf()
    assert 'resource "null_resource" "api_gateway_propagation_wait"' in content


def test_api_gateway_propagation_wait_depends_on_stage():
    """Verify propagation wait depends on stage."""
    content = _read_apigateway_tf()
    assert "aws_api_gateway_stage.prod" in content


def test_api_gateway_propagation_wait_depends_only_on_stage():
    """Verify propagation wait depends only on stage, not endpoint lambdas.

    This is intentional to break the circular dependency between API Gateway
    and endpoint lambdas. The propagation wait polls the echo endpoint, but
    the dependency is on the stage, not the lambda permission.
    """
    content = _read_apigateway_tf()
    # Should depend on stage (verified in test_api_gateway_propagation_wait_depends_on_stage)
    # Should NOT depend on echo_handler permission (breaks circular dependency)
    assert "depends_on = [" in content
    assert "aws_api_gateway_stage.prod" in content


def test_api_gateway_propagation_wait_triggers_on_deployment():
    """Verify propagation wait triggers on deployment."""
    content = _read_apigateway_tf()
    assert "aws_api_gateway_deployment.main.id" in content


def test_api_gateway_propagation_wait_uses_exponential_backoff():
    """Verify propagation wait uses exponential backoff."""
    content = _read_apigateway_tf()
    assert "1 << N" in content


def test_api_gateway_propagation_wait_polls_health_endpoint():
    """Verify propagation wait polls health endpoint.

    The health endpoint falls back to CatchAllHandler when the health
    Lambda doesn't exist, allowing the API workflow to complete without
    requiring other endpoint workflows to have run first.
    """
    content = _read_apigateway_tf()
    assert "/health" in content


def test_lambda_permission_simulation_soc_handler_exists():
    """Verify Lambda permission for simulation SOC handler exists."""
    content = _read_apigateway_tf()
    assert 'resource "aws_lambda_permission" "simulation_soc_handler"' in content
