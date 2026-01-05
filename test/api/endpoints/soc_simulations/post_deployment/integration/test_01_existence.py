"""Layer 1: Existence tests for simulation-soc endpoint.

Verify that resources created by this deployment exist.
"""
import pytest
from botocore.exceptions import ClientError


pytest_plugins = ['test_fixtures.aws']


def test_simulation_soc_handler_lambda_exists(lambda_client, shared_config):
    """Verify simulation-soc handler Lambda function exists."""
    function_name = shared_config.get("lambda_handler_names", {}).get(
        "simulation_soc", "TenULabsSimulationSocHandler"
    )
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        function_exists = response["Configuration"]["FunctionName"] == function_name
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            function_exists = False
        else:
            raise
    assert function_exists, f"Lambda function {function_name} does not exist"


def test_simulation_soc_handler_iam_role_exists(iam_client, shared_config):
    """Verify simulation-soc handler IAM role exists."""
    resource_prefix = shared_config.get("resource_prefix", "TenULabs")
    role_name = f"{resource_prefix}SimulationSocHandlerServiceRole"
    try:
        response = iam_client.get_role(RoleName=role_name)
        role_exists = response["Role"]["RoleName"] == role_name
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            role_exists = False
        else:
            raise
    assert role_exists, f"IAM role {role_name} does not exist"


def test_simulation_soc_handler_log_group_exists(handler_log_group):
    """Verify simulation-soc handler CloudWatch log group exists."""
    assert handler_log_group["exists"], (
        f"CloudWatch log group '{handler_log_group['name']}' does not exist"
    )
