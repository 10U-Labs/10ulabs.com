"""Fixtures for image_for_ecs_runners endpoint post-deployment integration tests."""
from test.api.endpoints.image_for_ecs_runners.endpoint.helpers import (
    ApiRequestConfig,
    ApiRequestParams,
    make_api_request,
)

import boto3
import pytest


@pytest.fixture(scope="session")
def lambda_client(request):
    """Create a Lambda client for the test session."""
    region = request.getfixturevalue('aws_region')
    return boto3.client("lambda", region_name=region)


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
