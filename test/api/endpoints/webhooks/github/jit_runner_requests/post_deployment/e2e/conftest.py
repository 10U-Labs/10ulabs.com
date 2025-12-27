"""Pytest fixtures for JIT runner requests webhook e2e tests."""
from test.api.conftest import endpoint_is_deployed

import pytest


DEFAULT_REQUEST_TIMEOUT = 10


# api_url and api_key fixtures are inherited from test_fixtures.aws


@pytest.fixture(name="github_pat", scope="module")
def github_pat_fixture(ssm_client, config):
    """Retrieve the GitHub PAT from SSM Parameter Store."""
    param_name = config.get('ssm_parameter_name_for_github_pat')
    param_response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
    result = None
    if param_response:
        result = param_response['Parameter']['Value']
    return result


def assert_circuit_breaker_state_in_response(response):
    """Assert that the response contains circuit breaker state.

    Used by circuit breaker tests - checks for 'state' field in the response
    from GET /v1/webhooks/github/jit-runner-requests/circuit-breaker endpoint.
    """
    data = response.json()
    assert "state" in data


def skip_if_endpoint_not_deployed(api_url, path, method="GET"):
    """Skip test if endpoint is not deployed."""
    if not endpoint_is_deployed(api_url, path, method):
        pytest.skip(f"Endpoint {path} not deployed")
