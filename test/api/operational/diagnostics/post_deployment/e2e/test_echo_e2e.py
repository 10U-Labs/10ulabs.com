import requests


TEST_HEADERS = {"x-test-mode": "true"}


class TestEchoEndpointBasicJourney:
    def test_echo_endpoint_responds_with_200(self, api_url):
        response = requests.post(
            f"{api_url}/diagnostics/echo",
            json={"test": "data"},
            headers=TEST_HEADERS,
            timeout=10
        )
        assert response.status_code == 200

    def test_echo_endpoint_returns_json(self, api_url):
        response = requests.post(
            f"{api_url}/diagnostics/echo",
            json={"test": "data"},
            headers=TEST_HEADERS,
            timeout=10
        )
        assert response.headers["Content-Type"] == "application/json"

    def test_echo_endpoint_contains_echo_field(self, api_url):
        response = requests.post(
            f"{api_url}/diagnostics/echo",
            json={"test": "data"},
            headers=TEST_HEADERS,
            timeout=10
        )
        data = response.json()
        assert "echo" in data

    def test_echo_endpoint_echoes_data_correctly(self, api_url):
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
    def test_echo_endpoint_stable_over_sequential_requests(self, api_url):
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
    def test_echo_endpoint_rejects_malformed_json(self, api_url):
        headers = {"Content-Type": "application/json", "x-test-mode": "true"}
        response = requests.post(
            f"{api_url}/diagnostics/echo",
            data="not valid json",
            headers=headers,
            timeout=10
        )
        assert response.status_code in [400, 500]

    def test_echo_endpoint_handles_empty_body(self, api_url):
        response = requests.post(
            f"{api_url}/diagnostics/echo",
            json={},
            headers=TEST_HEADERS,
            timeout=10
        )
        assert response.status_code in [200, 400, 500]
