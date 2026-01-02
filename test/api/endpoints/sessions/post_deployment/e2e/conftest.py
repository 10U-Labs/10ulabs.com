"""Pytest fixtures for sessions E2E tests.

E2E tests verify critical user journeys from end to end.
These tests make real HTTP requests to the deployed API.
"""
import pytest


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    """Provide the API URL for E2E tests."""
    return f"https://api.{config['domain_name']}"


@pytest.fixture(name="test_device_id", scope="module")
def test_device_id_fixture():
    """Provide a test device ID for E2E tests."""
    return "e2e-test-device"


@pytest.fixture(name="test_session_id", scope="module")
def test_session_id_fixture():
    """Provide a test session ID for E2E tests."""
    return "e2e-test-session-12345"
