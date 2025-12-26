"""Pytest fixtures for post-deployment integration tests.

These tests verify resources created by terraform apply exist and are
configured correctly.
"""
import pytest

from test_fixtures.aws import get_log_group_info

# Enable layer marker plugin for test ordering
pytest_plugins = ['pytest_layers']


@pytest.fixture(name="handler_function_name", scope="module")
def handler_function_name_fixture(config):
    """Get the Lambda function name from config."""
    return config.get(
        'ec2_images_handler_function_name',
        'TenULabsRunnersEC2ImagesHandler'
    )


@pytest.fixture(name="handler_log_group", scope="module")
def handler_log_group_fixture(logs_client, handler_function_name):
    """Get the Lambda handler log group info from CloudWatch."""
    log_group_name = f"/aws/lambda/{handler_function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(name="handler_role_name", scope="module")
def handler_role_name_fixture(handler_function_name):
    """Get the IAM role name from function name."""
    return f"{handler_function_name}ServiceRole"


@pytest.fixture(name="fetched_lambda_function", scope="module")
def fetched_lambda_function_fixture(lambda_client, handler_function_name):
    """Fetch the Lambda function details."""
    return lambda_client.get_function(FunctionName=handler_function_name)


@pytest.fixture(name="fetched_iam_role", scope="module")
def fetched_iam_role_fixture(iam_client, handler_role_name):
    """Fetch the IAM role details."""
    return iam_client.get_role(RoleName=handler_role_name)
