import requests
import pytest


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    return f"https://api.{config['domain_name']}"


@pytest.fixture(scope="module")
def website_url(config):
    return f"https://www.{config['domain_name']}"


@pytest.fixture(scope="module")
def test_device_id():
    return "e2e-test-device"


def save_and_load_config(api_url, config, device_id):
    post_response = requests.post(
        f"{api_url}/v1/rack-configurations",
        json={"configuration": config, "device_id": device_id},
        timeout=10
    )
    config_hash = post_response.json()["config_hash"]
    get_response = requests.get(
        f"{api_url}/v1/rack-configurations/{config_hash}",
        timeout=10
    )
    return config_hash, get_response
