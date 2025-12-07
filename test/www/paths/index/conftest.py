"""Pytest fixtures for www index tests."""
import sys
from pathlib import Path
from typing import Dict

import pytest
import requests

# Import shared parsing function to avoid duplication
# pylint: disable=import-error,wrong-import-position
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.conftest import parse_shared_module_outputs  # noqa: E402
# pylint: enable=import-error,wrong-import-position


@pytest.fixture(name="config", scope="module")
def config_fixture() -> Dict[str, str]:
    """Provide website configuration for tests."""
    shared = parse_shared_module_outputs()
    result = {}
    result['domain_name'] = shared.get('domain_name', '')
    result['website_fqdn'] = f"www.{shared.get('domain_name', '')}"
    return result


@pytest.fixture(name="website_url", scope="module")
def website_url_fixture(config):
    """Return the website URL from config."""
    return f"https://{config['website_fqdn']}"


@pytest.fixture(name="website_response", scope="module")
def website_response_fixture(website_url):
    """Fetch and return the website homepage response."""
    return requests.get(website_url, timeout=30)
