import requests


TEST_HEADERS = {"x-test-mode": "true"}


def test_echo_endpoint_accessible_without_auth(api_url):
    response = requests.post(f"{api_url}/v1/echo", json={"test": "data"}, headers=TEST_HEADERS, timeout=10)
    is_successful = response.status_code == 200
    assert is_successful


def test_echo_endpoint_returns_echoed_data(api_url):
    test_data = {"message": "hello", "number": 42}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    echoed_data_matches = data["echo"] == test_data
    assert echoed_data_matches


def test_echo_endpoint_with_unicode_returns_200(api_url):
    test_data = {"message": "Hello 世界 🌍"}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10)
    is_successful = response.status_code == 200
    assert is_successful


def test_echo_endpoint_with_unicode_preserves_characters(api_url):
    test_data = {"message": "Hello 世界 🌍"}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    unicode_preserved = data["echo"]["message"] == "Hello 世界 🌍"
    assert unicode_preserved


def test_echo_endpoint_with_large_payload(api_url):
    large_data = {"items": [{"id": i, "value": f"item-{i}"} for i in range(100)]}
    response = requests.post(f"{api_url}/v1/echo", json=large_data, headers=TEST_HEADERS, timeout=10)
    is_successful = response.status_code == 200
    assert is_successful


def test_echo_endpoint_preserves_string_type(api_url):
    test_data = {"string": "test"}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    string_preserved = data["echo"]["string"] == "test"
    assert string_preserved


def test_echo_endpoint_preserves_integer_type(api_url):
    test_data = {"number": 42}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    integer_preserved = data["echo"]["number"] == 42
    assert integer_preserved


def test_echo_endpoint_preserves_float_type(api_url):
    test_data = {"float": 3.14}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    float_preserved = data["echo"]["float"] == 3.14
    assert float_preserved


def test_echo_endpoint_preserves_boolean_type(api_url):
    test_data = {"boolean": True}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    boolean_preserved = data["echo"]["boolean"] is True
    assert boolean_preserved


def test_echo_endpoint_preserves_null_type(api_url):
    test_data = {"null": None}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    null_preserved = data["echo"]["null"] is None
    assert null_preserved
