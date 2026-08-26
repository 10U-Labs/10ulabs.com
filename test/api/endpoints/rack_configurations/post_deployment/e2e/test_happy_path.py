import requests

from .conftest import save_and_load_config


class TestConfigurationSaveJourney:
    def test_post_returns_200(self, api_url, test_device_id):
        config = {"rackHeight": 12, "rackCount": 3, "placedParts": []}
        response = requests.post(
            f"{api_url}/v1/rack-configurations",
            json={"configuration": config, "device_id": test_device_id},
            timeout=10
        )
        assert response.status_code == 200

    def test_post_returns_config_hash(self, api_url, test_device_id):
        config = {"rackHeight": 13, "rackCount": 3, "placedParts": []}
        response = requests.post(
            f"{api_url}/v1/rack-configurations",
            json={"configuration": config, "device_id": test_device_id},
            timeout=10
        )
        data = response.json()
        assert "config_hash" in data

    def test_config_hash_is_9_chars(self, api_url, test_device_id):
        config = {"rackHeight": 14, "rackCount": 3, "placedParts": []}
        response = requests.post(
            f"{api_url}/v1/rack-configurations",
            json={"configuration": config, "device_id": test_device_id},
            timeout=10
        )
        data = response.json()
        assert len(data["config_hash"]) == 9

    def test_config_hash_uses_valid_chars(self, api_url, test_device_id):
        config = {"rackHeight": 15, "rackCount": 3, "placedParts": []}
        response = requests.post(
            f"{api_url}/v1/rack-configurations",
            json={"configuration": config, "device_id": test_device_id},
            timeout=10
        )
        data = response.json()
        valid_chars = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        assert all(c in valid_chars for c in data["config_hash"])

    def test_same_config_same_hash(self, api_url, test_device_id):
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


class TestConfigurationLoadJourney:
    def test_roundtrip_saves_and_loads(self, api_url, test_device_id):
        config = {"rackHeight": 42, "rackCount": 5, "placedParts": []}
        _, get_response = save_and_load_config(api_url, config, test_device_id)
        assert get_response.status_code == 200

    def test_roundtrip_returns_correct_rack_height(self, api_url, test_device_id):
        config = {"rackHeight": 36, "rackCount": 4, "placedParts": []}
        _, get_response = save_and_load_config(api_url, config, test_device_id)
        assert get_response.json()["configuration"]["rackHeight"] == 36

    def test_roundtrip_returns_correct_rack_count(self, api_url, test_device_id):
        config = {"rackHeight": 24, "rackCount": 7, "placedParts": []}
        _, get_response = save_and_load_config(api_url, config, test_device_id)
        assert get_response.json()["configuration"]["rackCount"] == 7

    def test_roundtrip_preserves_placed_parts(self, api_url, test_device_id):
        part = {"type": "switch", "size": 1, "rackId": 1, "startSlot": 12}
        config = {"rackHeight": 18, "rackCount": 1, "placedParts": [part]}
        _, get_response = save_and_load_config(api_url, config, test_device_id)
        assert len(get_response.json()["configuration"]["placedParts"]) == 1

    def test_roundtrip_preserves_custom_name(self, api_url, test_device_id):
        part = {"type": "server", "size": 2, "rackId": 1, "startSlot": 1,
                "customName": "Web Server", "customColor": None}
        config = {"rackHeight": 19, "rackCount": 1, "placedParts": [part]}
        _, get_response = save_and_load_config(api_url, config, test_device_id)
        loaded = get_response.json()["configuration"]["placedParts"][0]
        assert loaded["customName"] == "Web Server"

    def test_roundtrip_preserves_custom_color(self, api_url, test_device_id):
        part = {"type": "server", "size": 2, "rackId": 1, "startSlot": 1,
                "customName": None, "customColor": "#3498db"}
        config = {"rackHeight": 20, "rackCount": 1, "placedParts": [part]}
        _, get_response = save_and_load_config(api_url, config, test_device_id)
        loaded = get_response.json()["configuration"]["placedParts"][0]
        assert loaded["customColor"] == "#3498db"


class TestCORSJourney:
    def test_options_returns_cors_headers(self, api_url):
        response = requests.options(
            f"{api_url}/v1/rack-configurations",
            timeout=10
        )
        assert response.status_code == 200

    def test_post_returns_cors_headers(self, api_url, test_device_id):
        config = {"rackHeight": 21, "rackCount": 3, "placedParts": []}
        response = requests.post(
            f"{api_url}/v1/rack-configurations",
            json={"configuration": config, "device_id": test_device_id},
            timeout=10
        )
        assert "Access-Control-Allow-Origin" in response.headers
