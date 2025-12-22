"""Fixtures for image_for_ecs_runners endpoint post-deployment integration tests."""
from test.api.endpoints.image_for_ecs_runners.endpoint.helpers import (
    ApiRequestConfig,
    ApiRequestParams,
    make_api_request,
)

import pytest

# Enable layer marker plugin for test ordering
pytest_plugins = ['pytest_layers']


@pytest.fixture(scope="session")
def api_request(request):
    """Provide a function to make API requests."""
    fqdn = request.getfixturevalue('api_fqdn')
    key = request.getfixturevalue('api_key')
    config = ApiRequestConfig(fqdn=fqdn, api_key=key, test_mode_default=True)

    def _make_request(path, method="GET", headers=None, body=None):
        params = ApiRequestParams(path=path, method=method, headers=headers, body=body)
        return make_api_request(config, params)

    return _make_request


@pytest.fixture(name="lambda_function", scope="module")
def lambda_function_fixture(lambda_client):
    """Find and return the Lambda function matching ImageForEcsRunners."""
    response = lambda_client.list_functions()
    matching = [
        f for f in response["Functions"]
        if "ImageForEcsRunners" in f["FunctionName"]
    ]
    if not matching:
        pytest.fail(
            "No Lambda function found matching 'ImageForEcsRunners'. "
            "Run terraform apply in src/api/endpoints/image_for_ecs_runners/"
        )
    return matching[0]


@pytest.fixture(name="lambda_config", scope="module")
def lambda_config_fixture(lambda_client, lambda_function):
    """Get the Lambda function configuration."""
    return lambda_client.get_function_configuration(
        FunctionName=lambda_function["FunctionName"]
    )


@pytest.fixture(name="env_vars", scope="module")
def env_vars_fixture(lambda_config):
    """Get environment variables from Lambda config."""
    return lambda_config.get("Environment", {}).get("Variables", {})
