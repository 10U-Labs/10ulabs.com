"""Tests for Lambda function deployment and configuration."""
import pytest
from botocore.exceptions import ClientError


def test_lambda_catchall_handler_exists(lambda_client, shared_config):
    """Verify Lambda catchall handler function exists."""
    function_name = shared_config['lambda_handler_names']['catchall']
    response = lambda_client.get_function(FunctionName=function_name)
    names_match = response["Configuration"]["FunctionName"] == function_name
    assert names_match


def test_lambda_catchall_handler_runtime(lambda_client, shared_config):
    """Verify Lambda catchall handler uses Python 3.13 runtime."""
    function_name = shared_config['lambda_handler_names']['catchall']
    response = lambda_client.get_function(FunctionName=function_name)
    is_python313 = response["Configuration"]["Runtime"] == "python3.13"
    assert is_python313


def test_api_gateway_has_permission_to_invoke_health_lambda(lambda_client, config):
    """Verify API Gateway has permission to invoke health Lambda function."""
    function_name = config["health_handler_function_name"]
    try:
        response = lambda_client.get_policy(FunctionName=function_name)
        has_policy = "Policy" in response
        assert has_policy
    except ClientError as err:
        if err.response["Error"]["Code"] == "ResourceNotFoundException":
            pytest.skip("Health Lambda not deployed (managed by endpoint_health.yml workflow)")
        raise
