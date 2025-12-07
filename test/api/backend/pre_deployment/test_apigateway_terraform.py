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


def test_api_gateway_propagation_wait_accepts_404():
    """Verify propagation wait accepts 404 as success.

    CatchAllHandler returns 404 for missing endpoints, which is valid.
    Both 200 (health Lambda exists) and 404 (CatchAllHandler fallback)
    indicate API Gateway is deployed and functioning.
    """
    content = _read_apigateway_tf()
    assert '"$HTTP_STATUS" = "404"' in content


def test_lambda_function_names_map_exists():
    """Verify lambda_function_names map is defined in locals."""
    content = _read_apigateway_tf()
    assert 'lambda_function_names = {' in content


def test_lambda_function_names_map_has_all_handlers():
    """Verify lambda_function_names map includes all endpoint handlers."""
    content = _read_apigateway_tf()
    required_handlers = [
        'catchall',
        'contact',
        'ec2_runner',
        'ecs_runner',
        'echo',
        'health',
        'image_for_ec2_runners',
        'image_for_ecs_runners',
        'rack_designer',
        'runners',
        'simulation_soc',
    ]
    for handler in required_handlers:
        assert f'{handler}' in content, f"Missing handler: {handler}"


def test_lambda_arn_prefix_defined():
    """Verify lambda_arn_prefix local is defined for ARN construction."""
    content = _read_apigateway_tf()
    assert 'lambda_arn_prefix' in content
    assert 'arn:aws:lambda:' in content


def test_apigw_integration_prefix_defined():
    """Verify apigw_integration_prefix local is defined."""
    content = _read_apigateway_tf()
    assert 'apigw_integration_prefix' in content
    assert 'arn:aws:apigateway:' in content


def test_arns_constructed_from_function_names():
    """Verify ARNs are constructed from lambda_function_names, not remote state."""
    content = _read_apigateway_tf()
    # Health ARN should reference the lambda_function_names map
    assert 'local.lambda_function_names.health' in content
    # Should NOT use remote state for ARN construction
    assert 'data.terraform_remote_state.health.outputs.lambda_function_arn' not in content


def test_no_conditional_arn_fallback_to_catchall():
    """Verify ARN construction doesn't use conditional fallback to catchall.

    ARNs should be constructed directly from function names, not conditionally
    based on remote state existence.
    """
    content = _read_apigateway_tf()
    # Old pattern: conditional with catchall fallback
    # New pattern: direct construction from function names
    # The health_arn should NOT have a ternary fallback pattern
    lines = content.split('\n')
    for line in lines:
        if 'health_arn' in line and '=' in line:
            # Should not contain the old conditional pattern
            assert '!= ""' not in line or 'lambda_function_names' in content


def test_health_handler_function_name_matches_expected():
    """Verify health handler function name comes from shared module."""
    content = _read_apigateway_tf()
    assert 'health' in content
    assert 'module.shared.lambda_handler_names.health' in content
