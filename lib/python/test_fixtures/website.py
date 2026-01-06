"""Website fixtures for pytest tests.

Use by adding to conftest.py:
    from test_fixtures.website import create_website_fixtures
    website_url, website_response = create_website_fixtures()

Requires a 'config' fixture that provides a dict with 'website_fqdn' key.
"""
from typing import Tuple

import pytest
import requests


def create_website_fixtures() -> Tuple:
    """Create website fixtures for e2e tests.

    Returns:
        Tuple of (website_url_fixture, website_response_fixture) fixtures
    """
    @pytest.fixture(name="website_url", scope="module")
    def _website_url_fixture(config):
        """Return the website URL from config."""
        return f"https://{config['website_fqdn']}"

    @pytest.fixture(name="website_response", scope="module")
    def _website_response_fixture(website_url):  # pylint: disable=redefined-outer-name
        """Fetch and return the website homepage response."""
        return requests.get(website_url, timeout=30)

    return _website_url_fixture, _website_response_fixture
