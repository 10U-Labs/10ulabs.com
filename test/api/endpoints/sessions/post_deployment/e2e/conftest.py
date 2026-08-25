"""Pytest fixtures for sessions E2E tests.

E2E tests verify critical user journeys from end to end.
These tests make real HTTP requests to the deployed API.
"""
import pytest


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config):
    """Provide sessions configuration for E2E tests."""
    return {
        "domain_name": shared_config["domain_name"],
        "api_fqdn": f"api.{shared_config['domain_name']}",
    }


@pytest.fixture(scope="module")
def api_url(config):
    """Provide the API URL for E2E tests."""
    return f"https://{config['api_fqdn']}"


@pytest.fixture(scope="module")
def test_device_id():
    """Provide a test device ID for E2E tests."""
    return "e2e-test-device"


@pytest.fixture(scope="module")
def test_session_id():
    """Provide a test session ID for E2E tests."""
    return "e2e-test-session-12345"
