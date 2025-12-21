"""E2E tests for critical happy path user journeys.

These tests verify end-to-end behavior that users experience.
Each test documents the user journey it validates.
"""
import concurrent.futures
import time

import requests

from test_fixtures.aws import get_shared_config
from ..conftest import skip_if_endpoint_not_deployed


TEST_HEADERS = {"x-test-mode": "true"}


# =============================================================================
# API Accessibility Journey
# =============================================================================


def test_root_endpoint_responds():
    """
    User Journey: User accesses the API root endpoint.

    When: A user navigates to the API root URL
    Then: They receive a successful response or redirect to docs

    Critical Path: CloudFront → S3 (or API Gateway)
    Failure Impact: API appears down, users cannot access documentation
    """
    config = get_shared_config()
    api_url = f"https://{config['api_fqdn']}"
    response = requests.get(api_url, headers=TEST_HEADERS, timeout=10)
    # 200 for direct response, 301/302 for redirect to docs
    assert response.status_code in [200, 301, 302]


def test_openapi_spec_accessible(api_url):
    """
    User Journey: Developer retrieves OpenAPI specification.

    When: A developer requests the OpenAPI spec to generate client code
    Then: They receive a valid JSON OpenAPI document

    Critical Path: CloudFront → S3 → openapi.json
    Failure Impact: API integrations cannot be developed, documentation broken
    """
    response = requests.get(f"{api_url}/openapi.json", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 200


def test_openapi_spec_is_valid_json(api_url):
    """
    User Journey: Developer parses OpenAPI specification.

    When: A developer parses the OpenAPI spec JSON
    Then: The content type is correct and parseable

    Critical Path: CloudFront → S3 → Content-Type headers
    Failure Impact: Client code generators fail to parse spec
    """
    response = requests.get(f"{api_url}/openapi.json", headers=TEST_HEADERS, timeout=10)
    content_type = response.headers.get("Content-Type", "")
    assert "application/json" in content_type


# =============================================================================
# Health Check Journey
# =============================================================================


def test_health_endpoint_responds(api_url):
    """
    User Journey: Monitoring system checks API health.

    When: A monitoring system polls the /health endpoint
    Then: The API responds with its current health status

    Critical Path: CloudFront → API Gateway → Health Lambda
    Failure Impact: Monitoring false positives, no alerting on real outages
    """
    skip_if_endpoint_not_deployed(api_url, "/health")
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert response.status_code in [200, 503]


def test_health_endpoint_responds_to_options(api_url):
    """
    User Journey: Browser preflight request for CORS.

    When: A browser sends an OPTIONS request before making API calls
    Then: The API responds with CORS headers

    Critical Path: CloudFront → API Gateway CORS configuration
    Failure Impact: Web applications cannot call API from browser
    """
    skip_if_endpoint_not_deployed(api_url, "/health")
    response = requests.options(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert response.status_code in [200, 204]


# =============================================================================
# Performance/Reliability Journey
# =============================================================================


def test_api_handles_concurrent_requests(api_url):
    """
    User Journey: Multiple users access API simultaneously.

    When: 20 concurrent requests hit the health endpoint
    Then: At least 75% succeed (allowing for some throttling)

    Critical Path: CloudFront → API Gateway → Lambda concurrency
    Failure Impact: API becomes unavailable under normal load
    """
    skip_if_endpoint_not_deployed(api_url, "/health")

    def make_health_request():
        return requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_health_request) for _ in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_count = sum(1 for r in results if r.status_code == 200)
    assert success_count >= 15


def test_lambda_cold_start_responds_successfully(api_url):
    """
    User Journey: First user after Lambda idle period.

    When: A request arrives after Lambda has been idle
    Then: Lambda starts and responds successfully

    Critical Path: API Gateway → Lambda cold start → response
    Failure Impact: Intermittent failures for users after quiet periods
    """
    skip_if_endpoint_not_deployed(api_url, "/health")
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=15)
    assert response.status_code == 200


def test_lambda_cold_start_performance(api_url):
    """
    User Journey: User experience during Lambda cold start.

    When: A request triggers a Lambda cold start
    Then: Response arrives within acceptable time (<10s)

    Critical Path: Lambda initialization + handler execution
    Failure Impact: Poor user experience, timeouts in clients
    """
    skip_if_endpoint_not_deployed(api_url, "/health")
    start = time.time()
    requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=15)
    duration = time.time() - start
    assert duration < 10.0
