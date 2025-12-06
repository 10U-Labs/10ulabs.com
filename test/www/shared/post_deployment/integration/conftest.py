"""Pytest fixtures for www_shared integration tests."""
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
