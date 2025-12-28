"""Pytest fixtures for post-deployment integration tests."""
from test.api.conftest import (
    endpoint_is_deployed,
    skip_if_endpoint_not_deployed,
)

import pytest

# Re-export for backwards compatibility
__all__ = ['endpoint_is_deployed', 'skip_if_endpoint_not_deployed']

# Note: dynamodb_client fixture is inherited from parent conftest.py


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    """Provide the API base URL."""
    return f"https://{config['api_fqdn']}"


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture(ssm_client):
    """Retrieve API key from SSM Parameter Store."""
    param_response = ssm_client.get_parameter(Name='/api/key', WithDecryption=True)
    return param_response['Parameter']['Value'] if param_response else None
