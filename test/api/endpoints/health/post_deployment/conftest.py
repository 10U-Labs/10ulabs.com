"""Pytest fixtures for health endpoint post-deployment tests."""
import pytest


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture(config):
    """Extract AWS region from configuration."""
    return config["aws_region"]


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    """Build API URL from configuration."""
    return f"https://{config['api_fqdn']}"
