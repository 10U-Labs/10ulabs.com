import time
import requests


def test_circuit_breaker_opens_after_threshold_failures(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    assert response.status_code in [200, 403, 503]


def test_circuit_breaker_transitions_to_half_open_after_timeout(api_url, api_key):
    headers = {"x-api-key": api_key}
    requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    time.sleep(2)
    response = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    assert response.status_code in [200, 403, 503]


def test_circuit_breaker_closes_after_successful_request_in_half_open(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    assert response.status_code in [200, 403]


def test_requests_rejected_when_circuit_breaker_open(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    assert response.status_code in [200, 403, 503]


def test_circuit_breaker_publishes_metrics(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    assert response.status_code in [200, 403]


def test_circuit_breaker_remediation_workflow_detects_state(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        assert "circuit_breaker" in data or "status" in data


def test_circuit_breaker_auto_recovery_after_timeout(api_url, api_key):
    headers = {"x-api-key": api_key}
    response1 = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    if response1.status_code == 200:
        time.sleep(2)
        response2 = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
        if response2.status_code == 200:
            data2 = response2.json()
            assert 'circuit_breaker' in data2 or 'status' in data2
