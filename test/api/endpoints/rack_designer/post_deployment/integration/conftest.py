"""Pytest fixtures for rack designer integration tests."""
import pytest


@pytest.fixture(name="website_url", scope="module")
def website_url_fixture(config):
    """Provide website URL for tests."""
    return f"https://www.{config['domain_name']}"


@pytest.fixture(name="test_device_id", scope="module")
def test_device_id_fixture():
    """Provide test device ID for tests."""
    return "integration-test-device"
