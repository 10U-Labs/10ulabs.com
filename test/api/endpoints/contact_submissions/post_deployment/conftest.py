"""Pytest fixtures for contact post-deployment tests.

Provides api_url fixture for e2e tests.
"""

import pytest


@pytest.fixture(scope="module")
def api_url(config):
    """Return API URL from config."""
    return f"https://{config['api_fqdn']}"
