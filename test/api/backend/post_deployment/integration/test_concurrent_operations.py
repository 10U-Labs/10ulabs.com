"""Tests for API concurrent operations and performance."""
import concurrent.futures
import time
import requests

from ..conftest import skip_if_endpoint_not_deployed


TEST_HEADERS = {"x-test-mode": "true"}


def test_api_handles_high_volume_concurrent_requests(api_url):
    """Verify API handles high volume of concurrent health requests."""
    skip_if_endpoint_not_deployed(api_url, "/health")

    def make_health_request():
        return requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_health_request) for _ in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    success_count = sum(1 for r in results if r.status_code == 200)
    assert success_count >= 15


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


def test_lambda_cold_start_responds_successfully(api_url):
    """Verify Lambda responds successfully on cold start."""
    skip_if_endpoint_not_deployed(api_url, "/health")
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=15)
    assert response.status_code == 200


def test_lambda_cold_start_performance(api_url):
    """Verify Lambda cold start completes within acceptable time."""
    skip_if_endpoint_not_deployed(api_url, "/health")
    start = time.time()
    requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=15)
    duration = time.time() - start
    assert duration < 10.0
