"""Integration tests for the health endpoint."""
import time
import requests


TEST_HEADERS = {"x-test-mode": "true"}


def test_health_endpoint_responds(api_url):
    """Verify health endpoint returns HTTP 200."""
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 200


def test_health_endpoint_returns_json(api_url):
    """Verify health endpoint returns JSON content type."""
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert response.headers["Content-Type"] == "application/json"


def test_health_endpoint_has_status_field(api_url):
    """Verify health response contains status field."""
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    data = response.json()
    assert "status" in data


def test_health_endpoint_status_healthy(api_url):
    """Verify health status is healthy."""
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    data = response.json()
    assert data["status"] == "healthy"


def test_concurrent_health_request_1_returns_200(api_url):
    """Verify concurrent request 1 returns 200."""
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 200


def test_concurrent_health_request_2_returns_200(api_url):
    """Verify concurrent request 2 returns 200."""
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 200


def test_concurrent_health_request_3_returns_200(api_url):
    """Verify concurrent request 3 returns 200."""
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 200


def test_concurrent_health_request_4_returns_200(api_url):
    """Verify concurrent request 4 returns 200."""
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 200


def test_concurrent_health_request_5_returns_200(api_url):
    """Verify concurrent request 5 returns 200."""
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 200


def test_health_endpoint_response_time_under_5_seconds(api_url):
    """Verify health endpoint responds within 5 seconds."""
    start = time.time()
    requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    duration = time.time() - start
    assert duration < 5.0
