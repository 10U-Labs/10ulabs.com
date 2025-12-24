"""Pytest fixtures for post-deployment integration tests.

Layer marker system and logs_client inherited from parent conftest.
"""

import pytest
from test_fixtures.aws import get_log_group_info


@pytest.fixture(scope="module")
def health_handler_log_group(logs_client, config):
    """Get the health handler log group info from CloudWatch."""
    function_name = config.get(
        'health_handler_function_name', 'TenULabsHealthHandler'
    )
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)
