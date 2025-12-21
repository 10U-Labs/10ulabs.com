"""Pytest fixtures for post-deployment integration tests.

Layer marker system and logs_client inherited from parent conftest.
"""

import pytest


@pytest.fixture(scope="module")
def health_handler_log_group(logs_client, config):
    """Get the health handler log group info from CloudWatch."""
    function_name = config.get(
        'health_handler_function_name', 'TenULabsHealthHandler'
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
