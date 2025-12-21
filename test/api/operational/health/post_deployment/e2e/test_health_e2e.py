"""E2E tests for the health endpoint.

E2E tests verify end-to-end user journeys through the deployed system.
They test the full path: HTTP request -> API Gateway -> Lambda -> Response.

These tests run in production and must be:
- Production-safe (read-only verification)
- Few in number (critical user journeys only)
- Fast to fail (aggressive timeouts)
"""

import time

import requests


TEST_HEADERS = {"x-test-mode": "true"}


class TestHealthEndpointBasicJourney:
    """Critical user journey: API health check returns expected response."""

    def test_health_endpoint_responds_with_200(self, api_url):
        """
        User Journey: External client checks API health status.

        When: A client sends GET /health
        Then: The API returns HTTP 200

        Critical Path: HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Clients cannot verify API availability
        """
        response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, api_url):
        """
        User Journey: External client receives properly formatted health response.

        When: A client sends GET /health
        Then: The response has JSON content type

        Critical Path: HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Clients cannot parse health response
        """
        response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        assert response.headers["Content-Type"] == "application/json"

    def test_health_endpoint_contains_status_field(self, api_url):
        """
        User Journey: Health response includes status information.

        When: A client sends GET /health
        Then: The response body contains 'status' field

        Critical Path: HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Clients cannot determine API health status
        """
        response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        data = response.json()
        assert "status" in data

    def test_health_endpoint_status_is_healthy(self, api_url):
        """
        User Journey: Healthy API reports healthy status.

        When: A client sends GET /health to a functioning API
        Then: The status field is 'healthy'

        Critical Path: HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Clients may incorrectly consider API down
        """
        response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        data = response.json()
        assert data["status"] == "healthy"


class TestHealthEndpointStabilityJourney:
    """Critical user journey: Health endpoint is stable under repeated requests."""

    def test_health_endpoint_stable_over_sequential_requests(self, api_url):
        """
        User Journey: Monitoring system polls health endpoint repeatedly.

        When: A monitoring system sends 5 sequential health checks
        Then: All requests return HTTP 200

        Critical Path: Multiple HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Monitoring alerts triggered by intermittent failures
        """
        responses = [
            requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
            for _ in range(5)
        ]
        statuses = [r.status_code for r in responses]
        assert all(s == 200 for s in statuses)

    def test_health_endpoint_consistent_response_body(self, api_url):
        """
        User Journey: Multiple health checks return consistent data.

        When: A client sends 3 sequential health checks
        Then: All responses have status 'healthy'

        Critical Path: Multiple HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Inconsistent health reporting confuses monitoring
        """
        responses = [
            requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
            for _ in range(3)
        ]
        bodies = [r.json() for r in responses]
        assert all(b["status"] == "healthy" for b in bodies)

    def test_health_endpoint_no_cold_start_degradation(self, api_url):
        """
        User Journey: Lambda cold starts don't cause failures.

        When: A client sends requests after potential cold start
        Then: Both first and second requests succeed equally

        Critical Path: HTTP -> API Gateway -> Lambda (cold/warm) -> Response
        Failure Impact: Cold starts cause monitoring false positives
        """
        first_response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        time.sleep(1)
        second_response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        assert first_response.status_code == second_response.status_code


class TestHealthEndpointPerformanceJourney:
    """Critical user journey: Health endpoint responds within acceptable time."""

    def test_health_endpoint_average_response_time_acceptable(self, api_url):
        """
        User Journey: Health checks complete quickly for responsive monitoring.

        When: A monitoring system sends 5 health checks
        Then: Average response time is under 2 seconds

        Critical Path: HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Slow responses cause monitoring timeouts
        """
        times = []
        for _ in range(5):
            start = time.time()
            requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
            times.append(time.time() - start)
        avg_time = sum(times) / len(times)
        assert avg_time < 2.0

    def test_health_endpoint_response_time_under_5_seconds(self, api_url):
        """
        User Journey: Single health check completes in reasonable time.

        When: A client sends GET /health
        Then: Response arrives within 5 seconds

        Critical Path: HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Clients timeout waiting for health response
        """
        start = time.time()
        requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
        duration = time.time() - start
        assert duration < 5.0


class TestHealthEndpointResponseFormatJourney:
    """Critical user journey: Health response contains expected structure."""

    def test_health_endpoint_returns_valid_json_structure(self, api_url):
        """
        User Journey: Client receives complete health information.

        When: A client sends GET /health
        Then: Response contains status, service, and version fields

        Critical Path: HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Clients cannot extract required health metadata
        """
        response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        body = response.json()
        required_fields = ["status", "service", "version"]
        assert all(field in body for field in required_fields)

    def test_health_endpoint_service_field_matches_expected(self, api_url):
        """
        User Journey: Client identifies correct service from health response.

        When: A client sends GET /health
        Then: Service field is '10U Labs API'

        Critical Path: HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Service discovery/registry issues
        """
        response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        body = response.json()
        assert body["service"] == "10U Labs API"

    def test_health_endpoint_version_field_format_valid(self, api_url):
        """
        User Journey: Client can parse API version information.

        When: A client sends GET /health
        Then: Version field follows semver format (x.y.z)

        Critical Path: HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Version-based compatibility checks fail
        """
        response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        body = response.json()
        version_parts = body["version"].split(".")
        assert len(version_parts) == 3
