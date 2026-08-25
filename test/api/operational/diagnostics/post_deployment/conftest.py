"""Pytest fixtures for echo post-deployment tests."""
import pytest


@pytest.fixture(scope="module")
def api_url(config):
    """Return API URL from config."""
    return f"https://{config['api_fqdn']}"
