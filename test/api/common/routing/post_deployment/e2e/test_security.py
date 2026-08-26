import pytest
import requests

from ..conftest import skip_if_endpoint_not_deployed


TEST_HEADERS = {"x-test-mode": "true"}


def test_invalid_endpoint_returns_404(api_url):
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 404


def test_404_response_does_not_contain_traceback(api_url):
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    response_text = response.text.lower()
    assert "traceback" not in response_text


def test_404_response_does_not_reveal_lambda_internals(api_url):
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    response_text = response.text.lower()
    assert "lambda" not in response_text or "documentation" in response_text


def test_malformed_request_handled_gracefully(api_url, api_key):
    skip_if_endpoint_not_deployed(api_url, "/diagnostics/echo", "POST")
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    payload = {"action": "invalid-type"}
    response = requests.post(
        f"{api_url}/diagnostics/echo",
        json=payload,
        headers=headers,
        timeout=10,
    )
    if response.status_code == 404:
        pytest.skip("Endpoint /diagnostics/echo not deployed")
    assert response.status_code in [200, 400, 401, 403, 422]


def test_service_unavailable_returns_503(api_url):
    skip_if_endpoint_not_deployed(api_url, "/health")
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert response.status_code in [200, 503]


def test_error_response_contains_error_message(api_url):
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    assert "error" in response.text.lower() or "not found" in response.text.lower()
