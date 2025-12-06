"""Pytest fixtures for echo post-deployment tests."""
import boto3
import pytest


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture(config):
    """Return AWS region from config."""
    return config["aws_region"]


@pytest.fixture(name="ssm_client", scope="module")
def ssm_client_fixture(aws_region):
    """Create SSM client for AWS region."""
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    """Return API URL from config."""
    return f"https://{config['api_fqdn']}"
