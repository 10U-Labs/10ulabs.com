"""Pytest fixtures for www index tests."""
import importlib.util
from pathlib import Path
from typing import Dict

import pytest
import requests


def _load_shared_conftest():
    """Load shared conftest module dynamically to avoid import order issues."""
    shared_path = Path(__file__).parent.parent.parent / "shared" / "conftest.py"
    spec = importlib.util.spec_from_file_location("shared_conftest", shared_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_shared = _load_shared_conftest()
parse_shared_module_outputs = _shared.parse_shared_module_outputs


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
