"""Pytest fixtures for www index tests."""
from typing import Dict

import pytest
import requests


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Provide website configuration for tests."""
    result = {}
    result['domain_name'] = shared_config.get('domain_name', '')
    result['website_fqdn'] = f"www.{shared_config.get('domain_name', '')}"
    return result


@pytest.fixture(name="website_url", scope="module")
def website_url_fixture(config):
    """Return the website URL from config."""
    return f"https://{config['website_fqdn']}"


@pytest.fixture(name="website_response", scope="module")
def website_response_fixture(website_url):
    """Fetch and return the website homepage response."""
    return requests.get(website_url, timeout=30)
