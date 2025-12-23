"""Pytest fixtures for contact endpoint post-deployment integration tests.

Layer marker system and AWS clients inherited from parent conftest.
"""

import pytest


@pytest.fixture(scope="module")
def contact_handler_function_name(shared_config):
    """Get the contact handler Lambda function name."""
    return shared_config.get("lambda_handler_names", {}).get(
        "contact", "TenULabsContactHandler"
    )


@pytest.fixture(scope="module")
def contact_handler_log_group(request, logs_client):
    """Get the contact handler log group info from CloudWatch."""
    function_name = request.getfixturevalue("contact_handler_function_name")
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


@pytest.fixture(scope="module")
def contact_handler_env_vars(request, lambda_client):
    """Get the contact handler Lambda environment variables."""
    function_name = request.getfixturevalue("contact_handler_function_name")
    response = lambda_client.get_function(FunctionName=function_name)
    return response["Configuration"].get("Environment", {}).get("Variables", {})
