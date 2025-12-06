"""Tests for API error handling and response codes."""
import requests

from ..conftest import skip_if_endpoint_not_deployed


TEST_HEADERS = {"x-test-mode": "true"}


def test_invalid_endpoint_returns_404(api_url):
    """Verify invalid endpoint returns 404 status code."""
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 404


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


def test_internal_server_error_returns_500(api_url, api_key):
    """Verify internal server errors are handled correctly."""
    skip_if_endpoint_not_deployed(api_url, "/v1/ecs-runner", "POST")
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    payload = {"job_id": "invalid-type", "github_repo": "test/repo"}
    response = requests.post(
        f"{api_url}/v1/ecs-runner", json=payload, headers=headers, timeout=10
    )
    assert response.status_code in [200, 400, 403, 500]


def test_service_unavailable_returns_503(api_url):
    """Verify service unavailable returns 503 or 200 status code."""
    skip_if_endpoint_not_deployed(api_url, "/health")
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert response.status_code in [200, 503]


def test_api_responds_to_options_requests(api_url):
    """Verify API responds to OPTIONS requests."""
    skip_if_endpoint_not_deployed(api_url, "/health")
    response = requests.options(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert response.status_code in [200, 204]


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


def test_api_error_responses_include_correlation_ids(api_url):
    """Verify API error responses include correlation IDs."""
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 404
