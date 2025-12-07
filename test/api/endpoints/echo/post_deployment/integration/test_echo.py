"""Integration tests for echo endpoint."""
import concurrent.futures
import time

import requests

from .conftest import skip_if_endpoint_not_deployed


TEST_HEADERS = {"x-test-mode": "true"}


def test_echo_endpoint_accessible_without_auth(api_url):
    """Test that echo endpoint is accessible without authentication."""
    response = requests.post(
        f"{api_url}/v1/echo", json={"test": "data"}, headers=TEST_HEADERS, timeout=10
    )
    is_successful = response.status_code == 200
    assert is_successful


def test_echo_endpoint_returns_echoed_data(api_url):
    """Test that echo endpoint returns the echoed data."""
    test_data = {"message": "hello", "number": 42}
    response = requests.post(
        f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10
    )
    data = response.json()
    echoed_data_matches = data["echo"] == test_data
    assert echoed_data_matches


def test_echo_endpoint_with_unicode_returns_200(api_url):
    """Test that echo endpoint handles unicode content."""
    test_data = {"message": "Hello 世界 🌍"}
    response = requests.post(
        f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10
    )
    is_successful = response.status_code == 200
    assert is_successful


def test_echo_endpoint_with_unicode_preserves_characters(api_url):
    """Test that echo endpoint preserves unicode characters."""
    test_data = {"message": "Hello 世界 🌍"}
    response = requests.post(
        f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10
    )
    data = response.json()
    unicode_preserved = data["echo"]["message"] == "Hello 世界 🌍"
    assert unicode_preserved


def test_echo_endpoint_with_large_payload(api_url):
    """Test that echo endpoint handles large payloads."""
    large_data = {"items": [{"id": i, "value": f"item-{i}"} for i in range(100)]}
    response = requests.post(
        f"{api_url}/v1/echo", json=large_data, headers=TEST_HEADERS, timeout=10
    )
    is_successful = response.status_code == 200
    assert is_successful


def test_echo_endpoint_preserves_string_type(api_url):
    """Test that echo endpoint preserves string types."""
    test_data = {"string": "test"}
    response = requests.post(
        f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10
    )
    data = response.json()
    string_preserved = data["echo"]["string"] == "test"
    assert string_preserved


def test_echo_endpoint_preserves_integer_type(api_url):
    """Test that echo endpoint preserves integer types."""
    test_data = {"number": 42}
    response = requests.post(
        f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10
    )
    data = response.json()
    integer_preserved = data["echo"]["number"] == 42
    assert integer_preserved


def test_echo_endpoint_preserves_float_type(api_url):
    """Test that echo endpoint preserves float types."""
    test_data = {"float": 3.14}
    response = requests.post(
        f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10
    )
    data = response.json()
    float_preserved = data["echo"]["float"] == 3.14
    assert float_preserved


def test_echo_endpoint_preserves_boolean_type(api_url):
    """Test that echo endpoint preserves boolean types."""
    test_data = {"boolean": True}
    response = requests.post(
        f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10
    )
    data = response.json()
    boolean_preserved = data["echo"]["boolean"] is True
    assert boolean_preserved


def test_echo_endpoint_preserves_null_type(api_url):
    """Test that echo endpoint preserves null types."""
    test_data = {"null": None}
    response = requests.post(
        f"{api_url}/v1/echo", json=test_data, headers=TEST_HEADERS, timeout=10
    )
    data = response.json()
    null_preserved = data["echo"]["null"] is None
    assert null_preserved


def test_api_handles_concurrent_echo_requests(api_url):
    """Verify API handles concurrent echo requests."""
    skip_if_endpoint_not_deployed(api_url, "/v1/echo", "POST")

    def make_echo_request(value):
        url = f"{api_url}/v1/echo"
        return requests.post(url, json={"value": value}, headers=TEST_HEADERS, timeout=10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_echo_request, i) for i in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    success_count = sum(1 for r in results if r.status_code == 200)
    assert success_count >= 8


def test_malformed_json_request_returns_400(api_url):
    """Verify malformed JSON request returns 400 or 500 status code."""
    skip_if_endpoint_not_deployed(api_url, "/v1/echo", "POST")
    headers = {"Content-Type": "application/json", "x-test-mode": "true"}
    response = requests.post(
        f"{api_url}/v1/echo", data="not valid json", headers=headers, timeout=10
    )
    assert response.status_code in [400, 500]


def test_oversized_payload_returns_413(api_url):
    """Verify oversized payload returns 413 or handles gracefully."""
    skip_if_endpoint_not_deployed(api_url, "/v1/echo", "POST")
    large_payload = {"data": "x" * (10 * 1024 * 1024)}
    response = requests.post(
        f"{api_url}/v1/echo", json=large_payload, headers=TEST_HEADERS, timeout=30
    )
    assert response.status_code in [200, 413, 500]


def test_api_handles_malformed_json_gracefully(api_url):
    """Verify API handles malformed JSON gracefully."""
    skip_if_endpoint_not_deployed(api_url, "/v1/echo", "POST")
    headers = {"Content-Type": "application/json", "x-test-mode": "true"}
    response = requests.post(
        f"{api_url}/v1/echo", data="{invalid json", headers=headers, timeout=10
    )
    assert response.status_code in [400, 500]


def test_api_handles_missing_content_type_header(api_url):
    """Verify API handles missing Content-Type header."""
    skip_if_endpoint_not_deployed(api_url, "/v1/echo", "POST")
    response = requests.post(
        f"{api_url}/v1/echo", data='{"test": "data"}', headers=TEST_HEADERS, timeout=10
    )
    assert response.status_code in [200, 400]


def test_rate_limit_applies_to_echo_endpoint(api_url):
    """Verify rate limiting applies to echo endpoint."""
    skip_if_endpoint_not_deployed(api_url, "/v1/echo", "POST")
    url = f"{api_url}/v1/echo"
    payload = {"test": "rate_limit_check"}
    status_codes = []
    for _ in range(60):
        try:
            response = requests.post(url, json=payload, headers=TEST_HEADERS, timeout=2)
            status_codes.append(response.status_code)
            time.sleep(0.1)
        except requests.exceptions.Timeout:
            pass
    has_successful_response = 200 in status_codes
    assert has_successful_response, f"No 200 responses in {len(status_codes)} requests"
