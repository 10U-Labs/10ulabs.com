"""Pytest fixtures for rack designer E2E tests.

E2E tests verify critical user journeys from end to end.
These tests make real HTTP requests to the deployed API and frontend.
"""
import pytest


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    """Provide the API URL for E2E tests."""
    return f"https://api.{config['domain_name']}"


@pytest.fixture(name="website_url", scope="module")
def website_url_fixture(config):
    """Provide the website URL for E2E tests."""
    return f"https://www.{config['domain_name']}"


@pytest.fixture(name="test_device_id", scope="module")
def test_device_id_fixture():
    """Provide a test device ID for E2E tests."""
    return "e2e-test-device"


def create_test_configuration(rack_height=12, rack_count=3, placed_parts=None):
    """Create a valid rack configuration for testing.

    Args:
        rack_height: Height of the rack (1-42).
        rack_count: Number of racks (>= 1).
        placed_parts: List of placed parts, defaults to empty list.

    Returns:
        Dictionary with valid rack configuration.
    """
    return {
        "rackHeight": rack_height,
        "rackCount": rack_count,
        "placedParts": placed_parts or []
    }


def create_test_payload(config=None, device_id="e2e-test-device"):
    """Create a valid API payload for testing.

    Args:
        config: Rack configuration dictionary, defaults to basic config.
        device_id: Device identifier for tracking.

    Returns:
        Dictionary with configuration and device_id.
    """
    return {
        "configuration": config or create_test_configuration(),
        "device_id": device_id
    }
