"""Pytest fixtures for runners e2e tests."""
from test.api.conftest import endpoint_is_deployed

import requests

import pytest


DEFAULT_REQUEST_TIMEOUT = 10


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    """Provide the API URL from config."""
    return f"https://{config['api_fqdn']}"


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture(ssm_client):
    """Retrieve the API key from SSM Parameter Store."""
    param_response = ssm_client.get_parameter(Name='/api/key', WithDecryption=True)
    result = None
    if param_response:
        result = param_response['Parameter']['Value']
    return result


@pytest.fixture(name="github_pat", scope="module")
def github_pat_fixture(ssm_client, config):
    """Retrieve the GitHub PAT from SSM Parameter Store."""
    param_name = config.get('ssm_parameter_name_for_github_pat')
    param_response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
    result = None
    if param_response:
        result = param_response['Parameter']['Value']
    return result


def make_health_check_request(api_url, api_key):
    """Make an HTTP request to the health check endpoint."""
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    return requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)


def assert_circuit_breaker_state_in_response(response):
    """Assert that the response contains circuit breaker state.

    Used by circuit breaker tests - checks for 'state' field in the response
    from GET /v1/runners/circuit-breaker endpoint.
    """
    data = response.json()
    assert "state" in data


def assert_health_status_in_response(response):
    """Assert that the health response contains status field.

    Used by health endpoint tests - checks for 'status' field in the response
    from GET /v1/runners/health endpoint.
    """
    data = response.json()
    assert data["status"] == "healthy"


def skip_if_endpoint_not_deployed(api_url, path, method="GET"):
    """Skip test if endpoint is not deployed."""
    if not endpoint_is_deployed(api_url, path, method):
        pytest.skip(f"Endpoint {path} not deployed")
