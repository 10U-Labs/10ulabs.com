"""Pytest fixtures for post-deployment integration tests."""
from test.api.conftest import (
    endpoint_is_deployed,
    skip_if_endpoint_not_deployed,
)

import boto3
import pytest

# Re-export for backwards compatibility
__all__ = ['endpoint_is_deployed', 'skip_if_endpoint_not_deployed']


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture(config):
    """Provide AWS region from config."""
    return config["aws_region"]


@pytest.fixture(name="ssm_client", scope="module")
def ssm_client_fixture(aws_region):
    """Provide SSM client for the configured region."""
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(name="dynamodb_client", scope="module")
def dynamodb_client_fixture(aws_region):
    """Provide DynamoDB client for the configured region."""
    return boto3.client("dynamodb", region_name=aws_region)


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    """Provide the API base URL."""
    return f"https://{config['api_fqdn']}"


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture(ssm_client):
    """Retrieve API key from SSM Parameter Store."""
    param_response = ssm_client.get_parameter(Name='/api/key', WithDecryption=True)
    return param_response['Parameter']['Value'] if param_response else None
