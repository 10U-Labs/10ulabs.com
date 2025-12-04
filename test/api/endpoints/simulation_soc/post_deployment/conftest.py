"""Pytest fixtures for simulation-soc post-deployment tests."""
import boto3
import pytest


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture(config):
    """Get the AWS region from the test configuration."""
    return config["aws_region"]


@pytest.fixture(name="ssm_client", scope="module")
def ssm_client_fixture(aws_region):
    """Create a boto3 SSM client for the given AWS region."""
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    """Build the API URL from the test configuration."""
    return f"https://{config['api_fqdn']}"
