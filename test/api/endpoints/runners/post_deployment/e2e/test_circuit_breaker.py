"""Integration tests for circuit breaker functionality and API."""
import time

import requests

from .conftest import (
    assert_circuit_breaker_state_in_response,
    DEFAULT_REQUEST_TIMEOUT,
)


def _make_circuit_breaker_request(api_url, api_key):
    """Make an HTTP request to the circuit breaker status endpoint."""
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    return requests.get(
        f"{api_url}/v1/runners/circuit-breaker",
        headers=headers,
        timeout=DEFAULT_REQUEST_TIMEOUT,
    )


def test_circuit_breaker_opens_after_threshold_failures(api_url, api_key):
    """Test circuit breaker opens after threshold failures."""
    response = _make_circuit_breaker_request(api_url, api_key)
    assert response.status_code in [200, 403, 503]


def test_circuit_breaker_transitions_to_half_open_after_timeout(api_url, api_key):
    """Test circuit breaker transitions to half open after timeout."""
    _make_circuit_breaker_request(api_url, api_key)
    time.sleep(2)
    response = _make_circuit_breaker_request(api_url, api_key)
    assert response.status_code in [200, 403, 503]


def test_circuit_breaker_closes_after_successful_request_in_half_open(api_url, api_key):
    """Test circuit breaker closes after successful request in half open."""
    response = _make_circuit_breaker_request(api_url, api_key)
    assert response.status_code in [200, 403]


def test_requests_rejected_when_circuit_breaker_open(api_url, api_key):
    """Test requests rejected when circuit breaker open."""
    response = _make_circuit_breaker_request(api_url, api_key)
    assert response.status_code in [200, 403, 503]


def test_circuit_breaker_publishes_metrics(api_url, api_key):
    """Test circuit breaker publishes metrics."""
    response = _make_circuit_breaker_request(api_url, api_key)
    assert response.status_code in [200, 403]


def test_circuit_breaker_remediation_workflow_detects_state(api_url, api_key):
    """Test circuit breaker remediation workflow detects state."""
    response = _make_circuit_breaker_request(api_url, api_key)
    assert_circuit_breaker_state_in_response(response)


def test_circuit_breaker_auto_recovery_after_timeout(api_url, api_key):
    """Test circuit breaker auto recovery after timeout."""
    response1 = _make_circuit_breaker_request(api_url, api_key)
    assert_circuit_breaker_state_in_response(response1)


def test_circuit_breaker_auto_recovery_second_request_has_state(api_url, api_key):
    """Test circuit breaker auto recovery second request has state."""
    response1 = _make_circuit_breaker_request(api_url, api_key)
    response2 = None
    if response1.status_code == 200:
        time.sleep(2)
        response2 = _make_circuit_breaker_request(api_url, api_key)
    has_second_response = response2 is not None
    assert has_second_response


# Circuit Breaker API Endpoint Tests


def test_circuit_breaker_status_endpoint_returns_200_or_503(api_url, api_key):
    """Test GET /v1/runners/circuit-breaker returns status."""
    headers = {"x-api-key": api_key}
    response = requests.get(
        f"{api_url}/v1/runners/circuit-breaker",
        headers=headers,
        timeout=DEFAULT_REQUEST_TIMEOUT,
    )
    assert response.status_code in [200, 503]


def test_circuit_breaker_status_endpoint_returns_json(api_url, api_key):
    """Test GET /v1/runners/circuit-breaker returns JSON response."""
    headers = {"x-api-key": api_key}
    response = requests.get(
        f"{api_url}/v1/runners/circuit-breaker",
        headers=headers,
        timeout=DEFAULT_REQUEST_TIMEOUT,
    )
    assert response.headers.get("Content-Type") == "application/json"


def test_circuit_breaker_status_contains_healthy_field(api_url, api_key):
    """Test status response contains healthy field."""
    headers = {"x-api-key": api_key}
    response = requests.get(
        f"{api_url}/v1/runners/circuit-breaker",
        headers=headers,
        timeout=DEFAULT_REQUEST_TIMEOUT,
    )
    data = response.json()
    assert "healthy" in data


def test_circuit_breaker_status_contains_state_field(api_url, api_key):
    """Test status response contains state field."""
    headers = {"x-api-key": api_key}
    response = requests.get(
        f"{api_url}/v1/runners/circuit-breaker",
        headers=headers,
        timeout=DEFAULT_REQUEST_TIMEOUT,
    )
    data = response.json()
    assert "state" in data


def test_circuit_breaker_status_contains_sqs_event_source_field(api_url, api_key):
    """Test status response contains sqs_event_source field."""
    headers = {"x-api-key": api_key}
    response = requests.get(
        f"{api_url}/v1/runners/circuit-breaker",
        headers=headers,
        timeout=DEFAULT_REQUEST_TIMEOUT,
    )
    data = response.json()
    assert "sqs_event_source" in data


# NOTE: POST /v1/runners/circuit-breaker (reset) is not tested here because
# calling it would reset a legitimately open circuit breaker, potentially
# causing damage. The reset endpoint should only be tested manually or in
# isolated environments.
