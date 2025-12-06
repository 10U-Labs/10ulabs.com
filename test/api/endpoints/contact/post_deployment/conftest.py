"""Pytest fixtures for contact post-deployment tests."""
import pytest


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture(config):
    """Return AWS region from config."""
    return config["aws_region"]


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    """Return API URL from config."""
    return f"https://{config['api_fqdn']}"
