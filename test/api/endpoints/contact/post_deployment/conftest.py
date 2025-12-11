"""Pytest fixtures for contact post-deployment tests."""
import pytest


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    """Return API URL from config."""
    return f"https://{config['api_fqdn']}"
