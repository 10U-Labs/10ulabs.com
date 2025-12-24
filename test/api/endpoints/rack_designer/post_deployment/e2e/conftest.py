"""Pytest fixtures for rack designer E2E tests.

E2E tests verify critical user journeys from end to end.
These tests make real HTTP requests to the deployed API and frontend.
"""
import requests
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


def save_and_load_config(api_url, config, device_id):
    """Save a configuration and retrieve it, returning the loaded data.

    Args:
        api_url: Base API URL.
        config: Configuration dictionary to save.
        device_id: Device identifier.

    Returns:
        Tuple of (config_hash, loaded_configuration_data).
    """
    post_response = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config, "device_id": device_id},
        timeout=10
    )
    config_hash = post_response.json()["config_hash"]
    get_response = requests.get(
        f"{api_url}/v1/rack-designer/configurations/{config_hash}",
        timeout=10
    )
    return config_hash, get_response
