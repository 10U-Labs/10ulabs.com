"""Website fixtures for pytest tests.

Use by adding to conftest.py:
    pytest_plugins = ['test_fixtures.website']

Requires a 'config' fixture that provides a dict with 'website_fqdn' key.
"""
import pytest
import requests


@pytest.fixture(name="website_url", scope="module")
def website_url_fixture(config):
    """Return the website URL from config."""
    return f"https://{config['website_fqdn']}"


@pytest.fixture(name="website_response", scope="module")
def website_response_fixture(website_url):
    """Fetch and return the website homepage response."""
    return requests.get(website_url, timeout=30)
