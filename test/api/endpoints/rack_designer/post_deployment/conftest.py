"""Pytest fixtures for rack designer post-deployment tests."""
import pytest


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture(config):
    """Provide AWS region for tests."""
    return config["aws_region"]


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    """Provide API URL for tests."""
    return f"https://{config['api_fqdn']}"
