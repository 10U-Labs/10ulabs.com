"""Pytest fixtures for rack designer post-deployment tests."""
import pytest


@pytest.fixture(scope="module")
def api_url(config):
    """Provide API URL for tests."""
    return f"https://{config['api_fqdn']}"
