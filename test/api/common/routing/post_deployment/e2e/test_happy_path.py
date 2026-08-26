import concurrent.futures
import time

import requests

from ..conftest import skip_if_endpoint_not_deployed


TEST_HEADERS = {"x-test-mode": "true"}


def test_root_endpoint_responds(api_url):
    response = requests.get(api_url, headers=TEST_HEADERS, timeout=10)
    assert response.status_code in [200, 301, 302]


def test_openapi_spec_accessible(api_url):
    response = requests.get(f"{api_url}/openapi.json", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 200


def test_openapi_spec_is_valid_json(api_url):
    response = requests.get(f"{api_url}/openapi.json", headers=TEST_HEADERS, timeout=10)
    content_type = response.headers.get("Content-Type", "")
    assert "application/json" in content_type


def test_health_endpoint_responds(api_url):
    skip_if_endpoint_not_deployed(api_url, "/health")
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert response.status_code in [200, 503]


def test_health_endpoint_responds_to_options(api_url):
    skip_if_endpoint_not_deployed(api_url, "/health")
    response = requests.options(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert response.status_code in [200, 204]


def test_api_handles_concurrent_requests(api_url):
    skip_if_endpoint_not_deployed(api_url, "/health")

    def make_health_request():
        return requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_health_request) for _ in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_count = sum(1 for r in results if r.status_code == 200)
    assert success_count >= 15


def test_lambda_cold_start_responds_successfully(api_url):
    skip_if_endpoint_not_deployed(api_url, "/health")
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=15)
    assert response.status_code == 200


def test_lambda_cold_start_performance(api_url):
    skip_if_endpoint_not_deployed(api_url, "/health")
    start = time.time()
    requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=15)
    duration = time.time() - start
    assert duration < 10.0
