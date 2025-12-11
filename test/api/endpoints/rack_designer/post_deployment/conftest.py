"""Pytest fixtures for rack designer post-deployment tests."""
import pytest


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    """Provide API URL for tests."""
    return f"https://{config['api_fqdn']}"
