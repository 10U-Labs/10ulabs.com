"""Pytest fixtures for post-deployment integration tests.

Layer marker system and logs_client inherited from parent conftest.
"""
from test.api.conftest import skip_if_endpoint_not_deployed

import boto3
import pytest

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
    response = logs_client.describe_log_groups(
        logGroupNamePrefix=log_group_name,
        limit=1
    )
    log_groups = response.get("logGroups", [])
    matching = [lg for lg in log_groups if lg["logGroupName"] == log_group_name]
    return {
        "name": log_group_name,
        "exists": len(matching) > 0,
        "retention": matching[0].get("retentionInDays") if matching else None
    }
