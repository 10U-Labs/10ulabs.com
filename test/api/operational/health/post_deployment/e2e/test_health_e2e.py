import time

import requests


TEST_HEADERS = {"x-test-mode": "true"}


class TestHealthEndpointBasicJourney:
    def test_health_endpoint_responds_with_200(self, api_url):
        response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, api_url):
        response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        assert response.headers["Content-Type"] == "application/json"

    def test_health_endpoint_contains_status_field(self, api_url):
        response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        data = response.json()
        assert "status" in data

    def test_health_endpoint_status_is_healthy(self, api_url):
        response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        data = response.json()
        assert data["status"] == "healthy"


class TestHealthEndpointStabilityJourney:
    def test_health_endpoint_stable_over_sequential_requests(self, api_url):
        responses = [
            requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
            for _ in range(5)
        ]
        statuses = [r.status_code for r in responses]
        assert all(s == 200 for s in statuses)

    def test_health_endpoint_consistent_response_body(self, api_url):
        responses = [
            requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
            for _ in range(3)
        ]
        bodies = [r.json() for r in responses]
        assert all(b["status"] == "healthy" for b in bodies)

    def test_health_endpoint_no_cold_start_degradation(self, api_url):
        first_response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        time.sleep(1)
        second_response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        assert first_response.status_code == second_response.status_code


class TestHealthEndpointPerformanceJourney:
    def test_health_endpoint_average_response_time_acceptable(self, api_url):
        times = []
        for _ in range(5):
            start = time.time()
            requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
            times.append(time.time() - start)
        avg_time = sum(times) / len(times)
        assert avg_time < 2.0

    def test_health_endpoint_response_time_under_5_seconds(self, api_url):
        start = time.time()
        requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
        duration = time.time() - start
        assert duration < 5.0


class TestHealthEndpointResponseFormatJourney:
    def test_health_endpoint_returns_valid_json_structure(self, api_url):
        response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        body = response.json()
        required_fields = ["status", "service", "version"]
        assert all(field in body for field in required_fields)

    def test_health_endpoint_service_field_matches_expected(self, api_url):
        response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        body = response.json()
        assert body["service"] == "10U Labs API"

    def test_health_endpoint_version_field_format_valid(self, api_url):
        response = requests.get(
            f"{api_url}/health", headers=TEST_HEADERS, timeout=10
        )
        body = response.json()
        version_parts = body["version"].split(".")
        assert len(version_parts) == 3
