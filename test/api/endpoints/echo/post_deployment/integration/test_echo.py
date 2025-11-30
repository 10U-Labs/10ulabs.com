import requests


TEST_HEADERS = {"x-test-mode": "true"}


def test_echo_endpoint_accessible_without_auth(api_url):
    response = requests.post(f"{api_url}/v1/echo", json={"test": "data"}, headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 200


def test_echo_endpoint_returns_echoed_data(api_url):
    test_data = {"message": "hello", "number": 42}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    assert data["echo"] == test_data


def test_echo_endpoint_with_unicode_returns_200(api_url):
    test_data = {"message": "Hello 世界 🌍"}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 200


def test_echo_endpoint_with_unicode_preserves_characters(api_url):
    test_data = {"message": "Hello 世界 🌍"}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    assert data["echo"]["message"] == "Hello 世界 🌍"


def test_echo_endpoint_with_large_payload(api_url):
    large_data = {"items": [{"id": i, "value": f"item-{i}"} for i in range(100)]}
    response = requests.post(f"{api_url}/v1/echo", json=large_data, headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 200


def test_echo_endpoint_preserves_string_type(api_url):
    test_data = {"string": "test"}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    assert data["echo"]["string"] == "test"


def test_echo_endpoint_preserves_integer_type(api_url):
    test_data = {"number": 42}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    assert data["echo"]["number"] == 42


def test_echo_endpoint_preserves_float_type(api_url):
    test_data = {"float": 3.14}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    assert data["echo"]["float"] == 3.14


def test_echo_endpoint_preserves_boolean_type(api_url):
    test_data = {"boolean": True}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    assert data["echo"]["boolean"] is True


def test_echo_endpoint_preserves_null_type(api_url):
    test_data = {"null": None}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    assert data["echo"]["null"] is None
