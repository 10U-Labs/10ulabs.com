"""Layer 3: Wiring tests for simulation-soc endpoint.

Verify that components are connected properly. Assumes existence and configuration passed.
"""
import json

import pytest

pytestmark = pytest.mark.layer(3)

pytest_plugins = ['test_fixtures.aws']


def test_simulation_soc_handler_has_iam_role_attached(lambda_client, shared_config):
    """Verify simulation-soc handler has IAM role attached."""
    function_name = shared_config.get("lambda_handler_names", {}).get(
        "simulation_soc", "TenULabsSimulationSocHandler"
    )
    response = lambda_client.get_function(FunctionName=function_name)
    role_arn = response["Configuration"].get("Role", "")
    has_role = len(role_arn) > 0 and "SimulationSocHandler" in role_arn
    assert has_role, f"Lambda {function_name} has unexpected role: {role_arn}"


def test_simulation_soc_handler_role_has_logs_policy(iam_client, shared_config):
    """Verify simulation-soc handler role has CloudWatch Logs permissions."""
    resource_prefix = shared_config.get("resource_prefix", "TenULabs")
    role_name = f"{resource_prefix}SimulationSocHandlerServiceRole"

    response = iam_client.list_attached_role_policies(RoleName=role_name)
    policy_arns = [p["PolicyArn"] for p in response.get("AttachedPolicies", [])]

    has_basic_execution = any(
        "AWSLambdaBasicExecutionRole" in arn for arn in policy_arns
    )
    assert has_basic_execution, (
        f"Role {role_name} does not have AWSLambdaBasicExecutionRole attached. "
        f"Attached policies: {policy_arns}"
    )


def test_simulation_soc_handler_has_api_gateway_permission(lambda_client, shared_config):
    """Verify simulation-soc handler has API Gateway invoke permission."""
    function_name = shared_config.get("lambda_handler_names", {}).get(
        "simulation_soc", "TenULabsSimulationSocHandler"
    )
    try:
        response = lambda_client.get_policy(FunctionName=function_name)
        policy = json.loads(response["Policy"])
        statements = policy.get("Statement", [])
        has_api_gateway = any(
            "apigateway" in stmt.get("Principal", {}).get("Service", "")
            or "apigateway" in str(stmt.get("Condition", {}))
            for stmt in statements
        )
    except lambda_client.exceptions.ResourceNotFoundException:
        has_api_gateway = False

    assert has_api_gateway, (
        f"Lambda {function_name} does not have API Gateway invoke permission"
    )


def test_simulation_soc_handler_has_google_client_id(lambda_client, shared_config):
    """Verify simulation-soc handler has GOOGLE_CLIENT_ID environment variable."""
    function_name = shared_config.get("lambda_handler_names", {}).get(
        "simulation_soc", "TenULabsSimulationSocHandler"
    )
    response = lambda_client.get_function_configuration(FunctionName=function_name)
    env_vars = response.get("Environment", {}).get("Variables", {})
    has_google_client_id = "GOOGLE_CLIENT_ID" in env_vars
    assert has_google_client_id, (
        f"Lambda {function_name} does not have GOOGLE_CLIENT_ID environment variable"
    )


def test_cloudwatch_log_group_name_matches_lambda(handler_log_group, shared_config):
    """Verify CloudWatch log group name matches Lambda function name pattern."""
    function_name = shared_config.get("lambda_handler_names", {}).get(
        "simulation_soc", "TenULabsSimulationSocHandler"
    )
    expected_prefix = f"/aws/lambda/{function_name}"
    log_group_name = handler_log_group["name"]
    names_match = log_group_name == expected_prefix
    assert names_match, (
        f"Log group name {log_group_name} does not match expected {expected_prefix}"
    )
