import requests
import pytest


@pytest.fixture(name="saved_configuration", scope="module")
def saved_configuration_fixture(api_url):
    config = {
        "rackHeight": 24,
        "rackCount": 3,
        "placedParts": [
            {"type": "server", "size": 2, "rackId": 1, "startSlot": 1, "customName": "Web Server", "customColor": "#3498db"},
            {"type": "nas", "size": 4, "rackId": 1, "startSlot": 10, "customName": "Storage", "customColor": "#9b59b6"},
            {"type": "switch", "size": 1, "rackId": 2, "startSlot": 24, "customName": None, "customColor": None}
        ]
    }
    response = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config},
        timeout=30
    )
    if response.status_code != 200:
        yield None
        return
    data = response.json()
    yield {
        "config_hash": data["config_hash"],
        "original_config": config
    }


def test_e2e_rack_designer_save_returns_hash(saved_configuration):
    assert saved_configuration is not None
    assert saved_configuration["config_hash"] is not None


def test_e2e_rack_designer_load_returns_success(saved_configuration, api_url):
    if saved_configuration is None:
        pytest.fail("Configuration not saved")
    config_hash = saved_configuration["config_hash"]
    response = requests.get(
        f"{api_url}/v1/rack-designer/configurations/{config_hash}",
        timeout=30
    )
    assert response.status_code == 200


def test_e2e_rack_designer_load_returns_correct_rack_height(saved_configuration, api_url):
    if saved_configuration is None:
        pytest.fail("Configuration not saved")
    config_hash = saved_configuration["config_hash"]
    response = requests.get(
        f"{api_url}/v1/rack-designer/configurations/{config_hash}",
        timeout=30
    )
    data = response.json()
    assert data["configuration"]["rackHeight"] == 24


def test_e2e_rack_designer_load_returns_correct_rack_count(saved_configuration, api_url):
    if saved_configuration is None:
        pytest.fail("Configuration not saved")
    config_hash = saved_configuration["config_hash"]
    response = requests.get(
        f"{api_url}/v1/rack-designer/configurations/{config_hash}",
        timeout=30
    )
    data = response.json()
    assert data["configuration"]["rackCount"] == 3


def test_e2e_rack_designer_load_returns_correct_parts_count(saved_configuration, api_url):
    if saved_configuration is None:
        pytest.fail("Configuration not saved")
    config_hash = saved_configuration["config_hash"]
    response = requests.get(
        f"{api_url}/v1/rack-designer/configurations/{config_hash}",
        timeout=30
    )
    data = response.json()
    assert len(data["configuration"]["placedParts"]) == 3


def test_e2e_rack_designer_load_preserves_custom_name(saved_configuration, api_url):
    if saved_configuration is None:
        pytest.fail("Configuration not saved")
    config_hash = saved_configuration["config_hash"]
    response = requests.get(
        f"{api_url}/v1/rack-designer/configurations/{config_hash}",
        timeout=30
    )
    data = response.json()
    first_part = data["configuration"]["placedParts"][0]
    assert first_part["customName"] == "Web Server"


def test_e2e_rack_designer_load_preserves_custom_color(saved_configuration, api_url):
    if saved_configuration is None:
        pytest.fail("Configuration not saved")
    config_hash = saved_configuration["config_hash"]
    response = requests.get(
        f"{api_url}/v1/rack-designer/configurations/{config_hash}",
        timeout=30
    )
    data = response.json()
    first_part = data["configuration"]["placedParts"][0]
    assert first_part["customColor"] == "#3498db"


def test_e2e_rack_designer_deterministic_hash(api_url):
    config = {"rackHeight": 10, "rackCount": 1, "placedParts": []}
    response1 = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config},
        timeout=30
    )
    response2 = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config},
        timeout=30
    )
    assert response1.json()["config_hash"] == response2.json()["config_hash"]
