"""Integration tests for contact endpoint."""
import time

import requests


INTEGRATION_TEST_HEADERS = {"x-test-mode": "true", "Content-Type": "application/json"}


def make_contact_request_body():
    """Create a contact request body for testing."""
    return {
        "name": "Integration Test User",
        "email": "integration@example.com",
        "message": "Integration test message.",
        "recaptcha_token": "integration-test-token"
    }


def test_contact_endpoint_responds(api_url):
    """Test that contact endpoint responds with 200."""
    payload = make_contact_request_body()
    response = requests.post(
        f"{api_url}/v1/contact",
        headers=INTEGRATION_TEST_HEADERS, json=payload, timeout=10
    )
    status_is_200 = response.status_code == 200
    assert status_is_200


def test_contact_endpoint_returns_json(api_url):
    """Test that contact endpoint returns JSON."""
    payload = make_contact_request_body()
    response = requests.post(
        f"{api_url}/v1/contact",
        headers=INTEGRATION_TEST_HEADERS, json=payload, timeout=10
    )
    is_json_content_type = response.headers["Content-Type"].startswith("application/json")
    assert is_json_content_type


def test_contact_endpoint_has_success_field(api_url):
    """Test that contact endpoint returns success field."""
    payload = make_contact_request_body()
    response = requests.post(
        f"{api_url}/v1/contact",
        headers=INTEGRATION_TEST_HEADERS, json=payload, timeout=10
    )
    data = response.json()
    has_success_field = "success" in data
    assert has_success_field


def test_contact_endpoint_success_true_in_test_mode(api_url):
    """Test that contact endpoint returns success true in test mode."""
    payload = make_contact_request_body()
    response = requests.post(
        f"{api_url}/v1/contact",
        headers=INTEGRATION_TEST_HEADERS, json=payload, timeout=10
    )
    data = response.json()
    success_is_true = data["success"] is True
    assert success_is_true


def test_contact_endpoint_returns_test_mode_flag(api_url):
    """Test that contact endpoint returns test_mode flag."""
    payload = make_contact_request_body()
    response = requests.post(
        f"{api_url}/v1/contact",
        headers=INTEGRATION_TEST_HEADERS, json=payload, timeout=10
    )
    data = response.json()
    test_mode_is_true = data.get("test_mode") is True
    assert test_mode_is_true


def test_contact_endpoint_response_time_under_5_seconds(api_url):
    """Test that contact endpoint responds within 5 seconds."""
    payload = make_contact_request_body()
    start = time.time()
    requests.post(
        f"{api_url}/v1/contact",
        headers=INTEGRATION_TEST_HEADERS, json=payload, timeout=10
    )
    duration = time.time() - start
    duration_under_5_seconds = duration < 5.0
    assert duration_under_5_seconds


def test_contact_endpoint_cors_header_present(api_url):
    """Test that contact endpoint includes CORS header."""
    payload = make_contact_request_body()
    response = requests.post(
        f"{api_url}/v1/contact",
        headers=INTEGRATION_TEST_HEADERS, json=payload, timeout=10
    )
    has_cors_header = "Access-Control-Allow-Origin" in response.headers
    assert has_cors_header


def test_contact_endpoint_options_returns_200(api_url):
    """Test that contact endpoint OPTIONS returns 200."""
    response = requests.options(f"{api_url}/v1/contact", timeout=10)
    status_is_200 = response.status_code == 200
    assert status_is_200


def test_contact_endpoint_rejects_missing_name(api_url):
    """Test that contact endpoint rejects missing name."""
    payload = make_contact_request_body()
    payload["name"] = ""
    response = requests.post(
        f"{api_url}/v1/contact",
        headers=INTEGRATION_TEST_HEADERS, json=payload, timeout=10
    )
    status_is_400 = response.status_code == 400
    assert status_is_400


def test_contact_endpoint_rejects_invalid_email(api_url):
    """Test that contact endpoint rejects invalid email."""
    payload = make_contact_request_body()
    payload["email"] = "not-an-email"
    response = requests.post(
        f"{api_url}/v1/contact",
        headers=INTEGRATION_TEST_HEADERS, json=payload, timeout=10
    )
    status_is_400 = response.status_code == 400
    assert status_is_400
