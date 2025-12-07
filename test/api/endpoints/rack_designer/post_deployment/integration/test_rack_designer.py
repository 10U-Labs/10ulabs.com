"""Integration tests for rack designer API endpoints."""
import requests


def test_rack_designer_post_returns_200(api_url, test_device_id):
    """Test that POST returns 200 status code."""
    config = {"rackHeight": 12, "rackCount": 3, "placedParts": []}
    response = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    assert response.status_code == 200


def test_rack_designer_post_returns_config_hash(api_url, test_device_id):
    """Test that POST returns a config_hash in response."""
    config = {"rackHeight": 12, "rackCount": 3, "placedParts": []}
    response = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    data = response.json()
    assert "config_hash" in data


def test_rack_designer_post_config_hash_is_9_chars(api_url, test_device_id):
    """Test that config_hash is exactly 9 characters."""
    config = {"rackHeight": 12, "rackCount": 3, "placedParts": []}
    response = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    data = response.json()
    assert len(data["config_hash"]) == 9


def test_rack_designer_post_config_hash_uses_valid_chars(api_url, test_device_id):
    """Test that config_hash uses only valid alphanumeric characters."""
    config = {"rackHeight": 12, "rackCount": 3, "placedParts": []}
    response = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    data = response.json()
    valid_chars = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    assert all(c in valid_chars for c in data["config_hash"])


def test_rack_designer_post_same_config_same_hash(api_url, test_device_id):
    """Test that same configuration produces same hash."""
    config = {"rackHeight": 24, "rackCount": 2, "placedParts": []}
    response1 = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    response2 = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    assert response1.json()["config_hash"] == response2.json()["config_hash"]


def test_rack_designer_post_missing_device_id_returns_400(api_url):
    """Test that POST without device_id returns 400."""
    config = {"rackHeight": 12, "rackCount": 3, "placedParts": []}
    response = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config},
        timeout=10
    )
    assert response.status_code == 400


def test_rack_designer_post_missing_configuration_returns_400(api_url, test_device_id):
    """Test that POST without configuration field returns 400."""
    response = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"device_id": test_device_id},
        timeout=10
    )
    assert response.status_code == 400


def test_rack_designer_post_invalid_configuration_returns_400(api_url, test_device_id):
    """Test that POST with invalid configuration returns 400."""
    config = {"rackCount": 3, "placedParts": []}
    response = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    assert response.status_code == 400


def test_rack_designer_get_not_found_returns_404(api_url):
    """Test that GET with non-existent hash returns 404."""
    response = requests.get(
        f"{api_url}/v1/rack-designer/configurations/NOTFOUND0",
        timeout=10
    )
    assert response.status_code == 404


def test_rack_designer_get_invalid_format_returns_400(api_url):
    """Test that GET with invalid hash format returns 400."""
    response = requests.get(
        f"{api_url}/v1/rack-designer/configurations/invalid",
        timeout=10
    )
    assert response.status_code == 400


def test_rack_designer_roundtrip_saves_and_loads(api_url, test_device_id):
    """Test that a configuration can be saved and retrieved correctly."""
    config = {
        "rackHeight": 42,
        "rackCount": 5,
        "placedParts": [{
            "type": "server", "size": 2, "rackId": 1, "startSlot": 1,
            "customName": None, "customColor": None
        }]
    }
    post_response = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    config_hash = post_response.json()["config_hash"]
    get_response = requests.get(
        f"{api_url}/v1/rack-designer/configurations/{config_hash}",
        timeout=10
    )
    assert get_response.status_code == 200


def test_rack_designer_roundtrip_returns_correct_config(api_url, test_device_id):
    """Test that retrieved config matches saved config."""
    config = {
        "rackHeight": 36,
        "rackCount": 4,
        "placedParts": [{
            "type": "nas", "size": 4, "rackId": 2, "startSlot": 5,
            "customName": "Storage", "customColor": "#ff0000"
        }]
    }
    post_response = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    config_hash = post_response.json()["config_hash"]
    get_response = requests.get(
        f"{api_url}/v1/rack-designer/configurations/{config_hash}",
        timeout=10
    )
    data = get_response.json()
    assert data["configuration"]["rackHeight"] == 36


def test_rack_designer_roundtrip_preserves_placed_parts(api_url, test_device_id):
    """Test that placed parts are preserved in roundtrip."""
    config = {
        "rackHeight": 12,
        "rackCount": 1,
        "placedParts": [{
            "type": "switch", "size": 1, "rackId": 1, "startSlot": 12,
            "customName": "Top Switch", "customColor": "#00ff00"
        }]
    }
    post_response = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    config_hash = post_response.json()["config_hash"]
    get_response = requests.get(
        f"{api_url}/v1/rack-designer/configurations/{config_hash}",
        timeout=10
    )
    data = get_response.json()
    assert len(data["configuration"]["placedParts"]) == 1


def test_rack_designer_options_returns_cors_headers(api_url):
    """Test that OPTIONS request returns CORS headers."""
    response = requests.options(
        f"{api_url}/v1/rack-designer/configurations",
        timeout=10
    )
    assert response.status_code == 200


def test_rack_designer_post_returns_cors_headers(api_url, test_device_id):
    """Test that POST request returns CORS headers."""
    config = {"rackHeight": 12, "rackCount": 3, "placedParts": []}
    response = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    assert "Access-Control-Allow-Origin" in response.headers


def test_rack_designer_roundtrip_returns_correct_rack_count(api_url, test_device_id):
    """Test that rack count is preserved in roundtrip."""
    config = {
        "rackHeight": 24,
        "rackCount": 3,
        "placedParts": []
    }
    post_response = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    config_hash = post_response.json()["config_hash"]
    get_response = requests.get(
        f"{api_url}/v1/rack-designer/configurations/{config_hash}",
        timeout=10
    )
    data = get_response.json()
    assert data["configuration"]["rackCount"] == 3


def test_rack_designer_roundtrip_preserves_custom_name(api_url, test_device_id):
    """Test that custom name is preserved in roundtrip."""
    config = {
        "rackHeight": 12,
        "rackCount": 1,
        "placedParts": [{
            "type": "server", "size": 2, "rackId": 1, "startSlot": 1,
            "customName": "Web Server", "customColor": None
        }]
    }
    post_response = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    config_hash = post_response.json()["config_hash"]
    get_response = requests.get(
        f"{api_url}/v1/rack-designer/configurations/{config_hash}",
        timeout=10
    )
    data = get_response.json()
    assert data["configuration"]["placedParts"][0]["customName"] == "Web Server"


def test_rack_designer_roundtrip_preserves_custom_color(api_url, test_device_id):
    """Test that custom color is preserved in roundtrip."""
    config = {
        "rackHeight": 12,
        "rackCount": 1,
        "placedParts": [{
            "type": "server", "size": 2, "rackId": 1, "startSlot": 1,
            "customName": None, "customColor": "#3498db"
        }]
    }
    post_response = requests.post(
        f"{api_url}/v1/rack-designer/configurations",
        json={"configuration": config, "device_id": test_device_id},
        timeout=10
    )
    config_hash = post_response.json()["config_hash"]
    get_response = requests.get(
        f"{api_url}/v1/rack-designer/configurations/{config_hash}",
        timeout=10
    )
    data = get_response.json()
    assert data["configuration"]["placedParts"][0]["customColor"] == "#3498db"
