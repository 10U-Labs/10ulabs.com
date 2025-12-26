"""Shared fixtures for runners/ecs/images post-deployment tests."""
from test.api.endpoints.runners.ecs.images.endpoint.helpers import (
    ApiRequestConfig,
    ApiRequestParams,
    get_api_fqdn,
    get_aws_region,
    get_ecr_repository,
    make_api_request,
)

import pytest


@pytest.fixture(scope="session")
def aws_region():
    """Provide the AWS region."""
    return get_aws_region()


@pytest.fixture(scope="session")
def api_fqdn():
    """Provide the API fully qualified domain name."""
    return get_api_fqdn()


@pytest.fixture(scope="session")
def ecr_repository_name():
    """Provide the ECR repository name."""
    return get_ecr_repository()


@pytest.fixture(name="api_key", scope="session")
def api_key_fixture(ssm_client):
    """Retrieve the API key from SSM Parameter Store."""
    param_response = ssm_client.get_parameter(Name='/api/key', WithDecryption=True)
    return param_response['Parameter']['Value']


def create_api_request_fixture(test_mode_param=False):
    """Factory to create api_request fixtures with different test_mode handling."""
    def _api_request(request):
        fqdn = request.getfixturevalue('api_fqdn')
        key = request.getfixturevalue('api_key')
        config = ApiRequestConfig(fqdn=fqdn, api_key=key, test_mode_default=True)

        def _make_request(path, method="GET", headers=None, body=None, test_mode=True):
            if test_mode_param:
                params = ApiRequestParams(
                    path=path, method=method, headers=headers,
                    body=body, test_mode=test_mode
                )
            else:
                params = ApiRequestParams(
                    path=path, method=method, headers=headers, body=body
                )
            return make_api_request(config, params)

        return _make_request

    return _api_request
