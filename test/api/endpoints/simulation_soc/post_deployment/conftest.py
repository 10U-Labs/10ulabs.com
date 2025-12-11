"""Pytest fixtures for simulation-soc post-deployment tests."""
import pytest


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    """Build the API URL from the test configuration."""
    return f"https://{config['api_fqdn']}"
