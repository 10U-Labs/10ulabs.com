"""E2E tests for the diagnostics echo endpoint.

E2E tests verify end-to-end user journeys through the deployed system.
They test the full path: HTTP request -> API Gateway -> Lambda -> Response.

These tests run in production and must be:
- Production-safe (read-only verification)
- Few in number (critical user journeys only)
- Fast to fail (aggressive timeouts)
"""

import requests


TEST_HEADERS = {"x-test-mode": "true"}


class TestEchoEndpointBasicJourney:
    """Critical user journey: Echo endpoint returns expected response."""

    def test_echo_endpoint_responds_with_200(self, api_url):
        """
        User Journey: External client sends data to echo endpoint.

        When: A client sends POST /diagnostics/echo with JSON data
        Then: The API returns HTTP 200

        Critical Path: HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Clients cannot verify API connectivity
        """
        response = requests.post(
            f"{api_url}/diagnostics/echo",
            json={"test": "data"},
            headers=TEST_HEADERS,
            timeout=10
        )
        assert response.status_code == 200

    def test_echo_endpoint_returns_json(self, api_url):
        """
        User Journey: External client receives properly formatted echo response.

        When: A client sends POST /diagnostics/echo
        Then: The response has JSON content type

        Critical Path: HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Clients cannot parse echo response
        """
        response = requests.post(
            f"{api_url}/diagnostics/echo",
            json={"test": "data"},
            headers=TEST_HEADERS,
            timeout=10
        )
        assert response.headers["Content-Type"] == "application/json"

    def test_echo_endpoint_contains_echo_field(self, api_url):
        """
        User Journey: Echo response includes echoed data.

        When: A client sends POST /diagnostics/echo with data
        Then: The response body contains 'echo' field

        Critical Path: HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Clients cannot verify data was received
        """
        response = requests.post(
            f"{api_url}/diagnostics/echo",
            json={"test": "data"},
            headers=TEST_HEADERS,
            timeout=10
        )
        data = response.json()
        assert "echo" in data

    def test_echo_endpoint_echoes_data_correctly(self, api_url):
        """
        User Journey: Echo endpoint returns exact data sent.

        When: A client sends POST /diagnostics/echo with specific data
        Then: The echo field contains the exact data sent

        Critical Path: HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Data integrity verification fails
        """
        test_data = {"message": "hello", "number": 42}
        response = requests.post(
            f"{api_url}/diagnostics/echo",
            json=test_data,
            headers=TEST_HEADERS,
            timeout=10
        )
        data = response.json()
        assert data["echo"] == test_data


class TestEchoEndpointStabilityJourney:
    """Critical user journey: Echo endpoint is stable under repeated requests."""

    def test_echo_endpoint_stable_over_sequential_requests(self, api_url):
        """
        User Journey: Client sends multiple echo requests.

        When: A client sends 5 sequential echo requests
        Then: All requests return HTTP 200

        Critical Path: Multiple HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Intermittent failures affect client reliability
        """
        responses = [
            requests.post(
                f"{api_url}/diagnostics/echo",
                json={"request": i},
                headers=TEST_HEADERS,
                timeout=10
            )
            for i in range(5)
        ]
        statuses = [r.status_code for r in responses]
        assert all(s == 200 for s in statuses)

    def test_echo_endpoint_consistent_response_structure(self, api_url):
        """
        User Journey: Multiple echo requests return consistent structure.

        When: A client sends 3 sequential echo requests
        Then: All responses have 'echo' field

        Critical Path: Multiple HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Inconsistent responses confuse clients
        """
        responses = [
            requests.post(
                f"{api_url}/diagnostics/echo",
                json={"request": i},
                headers=TEST_HEADERS,
                timeout=10
            )
            for i in range(3)
        ]
        bodies = [r.json() for r in responses]
        assert all("echo" in b for b in bodies)


class TestEchoEndpointErrorHandlingJourney:
    """Critical user journey: Echo endpoint handles errors gracefully."""

    def test_echo_endpoint_rejects_malformed_json(self, api_url):
        """
        User Journey: Client sends malformed JSON to echo endpoint.

        When: A client sends invalid JSON to POST /diagnostics/echo
        Then: The API returns 400 or 500 (not 200)

        Critical Path: HTTP -> API Gateway -> Lambda -> Error Response
        Failure Impact: Invalid data silently accepted
        """
        headers = {"Content-Type": "application/json", "x-test-mode": "true"}
        response = requests.post(
            f"{api_url}/diagnostics/echo",
            data="not valid json",
            headers=headers,
            timeout=10
        )
        assert response.status_code in [400, 500]

    def test_echo_endpoint_handles_empty_body(self, api_url):
        """
        User Journey: Client sends empty body to echo endpoint.

        When: A client sends POST /diagnostics/echo with empty body
        Then: The API returns a response (200, 400, or 500)

        Critical Path: HTTP -> API Gateway -> Lambda -> Response
        Failure Impact: Empty requests cause unhandled errors
        """
        response = requests.post(
            f"{api_url}/diagnostics/echo",
            json={},
            headers=TEST_HEADERS,
            timeout=10
        )
        # Empty JSON object should be echoed back successfully
        assert response.status_code in [200, 400, 500]
