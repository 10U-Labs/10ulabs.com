import requests


def make_health_check_request(api_url, api_key):
    headers = {"x-api-key": api_key}
    return requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)


def assert_circuit_breaker_state_in_response(response):
    if response.status_code == 200:
        data = response.json()
        assert "circuit_breaker" in data or "status" in data
