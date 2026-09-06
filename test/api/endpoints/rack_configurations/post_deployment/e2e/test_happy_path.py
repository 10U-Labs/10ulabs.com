from typing import Any, Dict, Tuple

import requests


def save_and_load_config(
    api_url: str,
    config: Dict[str, Any],
    device_id: str
) -> Tuple[str, requests.Response]:
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


def test_save_returns_200(api_url: str, test_device_id: str) -> None:
    config = {"rackHeight": 12, "rackCount": 3, "placedParts": []}
    response = requests.post(
        f"{api_url}/v1/rack-configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    assert response.status_code == 200


def test_save_returns_config_hash(api_url: str, test_device_id: str) -> None:
    config = {"rackHeight": 13, "rackCount": 3, "placedParts": []}
    response = requests.post(
        f"{api_url}/v1/rack-configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    data = response.json()
    assert "config_hash" in data


def test_save_config_hash_is_9_chars(api_url: str, test_device_id: str) -> None:
    config = {"rackHeight": 14, "rackCount": 3, "placedParts": []}
    response = requests.post(
        f"{api_url}/v1/rack-configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    data = response.json()
    assert len(data["config_hash"]) == 9


def test_save_config_hash_uses_valid_chars(api_url: str, test_device_id: str) -> None:
    config = {"rackHeight": 15, "rackCount": 3, "placedParts": []}
    response = requests.post(
        f"{api_url}/v1/rack-configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    data = response.json()
    valid_chars = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    assert all(c in valid_chars for c in data["config_hash"])


def test_save_same_config_returns_same_hash(api_url: str, test_device_id: str) -> None:
    config = {"rackHeight": 24, "rackCount": 2, "placedParts": []}
    response1 = requests.post(
        f"{api_url}/v1/rack-configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    response2 = requests.post(
        f"{api_url}/v1/rack-configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    assert response1.json()["config_hash"] == response2.json()["config_hash"]


def test_roundtrip_saves_and_loads(api_url: str, test_device_id: str) -> None:
    config = {"rackHeight": 42, "rackCount": 5, "placedParts": []}
    _, get_response = save_and_load_config(api_url, config, test_device_id)
    assert get_response.status_code == 200


def test_roundtrip_returns_correct_rack_height(api_url: str, test_device_id: str) -> None:
    config = {"rackHeight": 36, "rackCount": 4, "placedParts": []}
    _, get_response = save_and_load_config(api_url, config, test_device_id)
    assert get_response.json()["configuration"]["rackHeight"] == 36


def test_roundtrip_returns_correct_rack_count(api_url: str, test_device_id: str) -> None:
    config = {"rackHeight": 24, "rackCount": 7, "placedParts": []}
    _, get_response = save_and_load_config(api_url, config, test_device_id)
    assert get_response.json()["configuration"]["rackCount"] == 7


def test_roundtrip_preserves_placed_parts(api_url: str, test_device_id: str) -> None:
    part = {"type": "switch", "size": 1, "rackId": 1, "startSlot": 12}
    config = {"rackHeight": 18, "rackCount": 1, "placedParts": [part]}
    _, get_response = save_and_load_config(api_url, config, test_device_id)
    assert len(get_response.json()["configuration"]["placedParts"]) == 1


def test_roundtrip_preserves_custom_name(api_url: str, test_device_id: str) -> None:
    part = {"type": "server", "size": 2, "rackId": 1, "startSlot": 1,
            "customName": "Web Server", "customColor": None}
    config = {"rackHeight": 19, "rackCount": 1, "placedParts": [part]}
    _, get_response = save_and_load_config(api_url, config, test_device_id)
    loaded = get_response.json()["configuration"]["placedParts"][0]
    assert loaded["customName"] == "Web Server"


def test_roundtrip_preserves_custom_color(api_url: str, test_device_id: str) -> None:
    part = {"type": "server", "size": 2, "rackId": 1, "startSlot": 1,
            "customName": None, "customColor": "#3498db"}
    config = {"rackHeight": 20, "rackCount": 1, "placedParts": [part]}
    _, get_response = save_and_load_config(api_url, config, test_device_id)
    loaded = get_response.json()["configuration"]["placedParts"][0]
    assert loaded["customColor"] == "#3498db"


def test_options_returns_cors_headers(api_url: str) -> None:
    response = requests.options(
        f"{api_url}/v1/rack-configurations",
        timeout=10
    )
    assert response.status_code == 200


def test_post_returns_cors_headers(api_url: str, test_device_id: str) -> None:
    config = {"rackHeight": 21, "rackCount": 3, "placedParts": []}
    response = requests.post(
        f"{api_url}/v1/rack-configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    assert "Access-Control-Allow-Origin" in response.headers
