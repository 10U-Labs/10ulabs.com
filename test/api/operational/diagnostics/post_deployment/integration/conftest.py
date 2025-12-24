"""Pytest fixtures for post-deployment integration tests.

Layer marker system and logs_client inherited from parent conftest.
"""
from test.api.conftest import skip_if_endpoint_not_deployed

import boto3
import pytest
from test_fixtures.aws import get_log_group_info

# Re-export for local imports
__all__ = ['skip_if_endpoint_not_deployed']


@pytest.fixture(scope="session")
def iam_client(aws_region):
    """Create an IAM client."""
    return boto3.client("iam", region_name=aws_region)


@pytest.fixture(scope="module")
def diagnostics_handler_log_group(logs_client, config):
    """Get the diagnostics handler log group info from CloudWatch."""
    function_name = config.get(
        'diagnostics_handler_function_name', 'TenULabsDiagnosticsHandler'
    )
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)
