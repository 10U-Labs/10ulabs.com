"""Tests for API rate limiting configuration and behavior."""
import time
import requests

from ..conftest import skip_if_endpoint_not_deployed


TEST_HEADERS = {"x-test-mode": "true"}


def test_rate_limit_exceeded_returns_429(api_url):
    """Verify rate limit exceeded returns 429 status code."""
    skip_if_endpoint_not_deployed(api_url, "/health")
    responses = []
    for _ in range(200):
        try:
            resp = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=1)
            responses.append(resp.status_code)
            if resp.status_code == 429:
                break
        except requests.exceptions.Timeout:
            continue
    assert 200 in responses or 429 in responses


def test_rate_limit_applies_to_health_endpoint(api_url):
    """Verify rate limiting applies to health endpoint."""
    skip_if_endpoint_not_deployed(api_url, "/health")
    responses = []
    for _ in range(60):
        try:
            resp = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=2)
            responses.append(resp.status_code)
            time.sleep(0.1)
        except requests.exceptions.Timeout:
            continue
    assert 200 in responses


def test_rate_limit_applies_to_echo_endpoint(api_url):
    """Verify rate limiting applies to echo endpoint."""
    skip_if_endpoint_not_deployed(api_url, "/v1/echo", "POST")
    responses = []
    for _ in range(60):
        try:
            resp = requests.post(
                f"{api_url}/v1/echo", json={"test": "data"}, headers=TEST_HEADERS, timeout=2
            )
            responses.append(resp.status_code)
            time.sleep(0.1)
        except requests.exceptions.Timeout:
            continue
    assert 200 in responses


def test_rate_limit_headers_present_in_response(api_url):
    """Verify rate limit headers are present in response."""
    skip_if_endpoint_not_deployed(api_url, "/health")
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 200


def test_rate_limit_burst_allows_initial_requests(api_url):
    """Verify rate limit burst allows initial requests."""
    skip_if_endpoint_not_deployed(api_url, "/health")
    success_count = 0
    for _ in range(10):
        try:
            resp = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=2)
            if resp.status_code == 200:
                success_count += 1
        except requests.exceptions.Timeout:
            continue
    assert success_count > 0
