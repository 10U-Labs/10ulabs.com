import requests


def test_echo_endpoint_accessible_without_auth(api_url):
    response = requests.post(f"{api_url}/v1/echo", json={"test": "data"}, timeout=10)
    assert response.status_code == 200


def test_echo_endpoint_returns_echoed_data(api_url):
    test_data = {"message": "hello", "number": 42}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, timeout=10)
    data = response.json()
    assert data["echo"] == test_data


def test_echo_endpoint_with_unicode(api_url):
    test_data = {"message": "Hello 世界 🌍"}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, timeout=10)
    assert response.status_code == 200
    data = response.json()
    assert data["echo"]["message"] == "Hello 世界 🌍"


def test_echo_endpoint_with_large_payload(api_url):
    large_data = {"items": [{"id": i, "value": f"item-{i}"} for i in range(100)]}
    response = requests.post(f"{api_url}/v1/echo", json=large_data, timeout=10)
    assert response.status_code == 200


def test_echo_endpoint_preserves_data_types(api_url):
    test_data = {
        "string": "test",
        "number": 42,
        "float": 3.14,
        "boolean": True,
        "null": None
    }
    response = requests.post(f"{api_url}/v1/echo", json=test_data, timeout=10)
    data = response.json()
    echo = data["echo"]
    assert echo["string"] == "test"
    assert echo["number"] == 42
    assert echo["float"] == 3.14
    assert echo["boolean"] is True
    assert echo["null"] is None
