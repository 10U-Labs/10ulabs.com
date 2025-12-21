"""Pytest fixtures for www index tests."""
from typing import Dict

import pytest

pytest_plugins = ['test_fixtures.website']


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Provide website configuration for tests."""
    result = {}
    result['domain_name'] = shared_config.get('domain_name', '')
    result['website_fqdn'] = f"www.{shared_config.get('domain_name', '')}"
    return result
