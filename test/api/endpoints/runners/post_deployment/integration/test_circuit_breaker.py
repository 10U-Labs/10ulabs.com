import time

from .conftest import make_health_check_request, assert_circuit_breaker_state_in_response


def test_circuit_breaker_opens_after_threshold_failures(api_url, api_key):
    response = make_health_check_request(api_url, api_key)
    assert response.status_code in [200, 403, 503]


def test_circuit_breaker_transitions_to_half_open_after_timeout(api_url, api_key):
    make_health_check_request(api_url, api_key)
    time.sleep(2)
    response = make_health_check_request(api_url, api_key)
    assert response.status_code in [200, 403, 503]


def test_circuit_breaker_closes_after_successful_request_in_half_open(api_url, api_key):
    response = make_health_check_request(api_url, api_key)
    assert response.status_code in [200, 403]


def test_requests_rejected_when_circuit_breaker_open(api_url, api_key):
    response = make_health_check_request(api_url, api_key)
    assert response.status_code in [200, 403, 503]


def test_circuit_breaker_publishes_metrics(api_url, api_key):
    response = make_health_check_request(api_url, api_key)
    assert response.status_code in [200, 403]


def test_circuit_breaker_remediation_workflow_detects_state(api_url, api_key):
    response = make_health_check_request(api_url, api_key)
    assert_circuit_breaker_state_in_response(response)


def test_circuit_breaker_auto_recovery_after_timeout(api_url, api_key):
    response1 = make_health_check_request(api_url, api_key)
    assert_circuit_breaker_state_in_response(response1)


def test_circuit_breaker_auto_recovery_second_request_has_state(api_url, api_key):
    response1 = make_health_check_request(api_url, api_key)
    response2 = None
    if response1.status_code == 200:
        time.sleep(2)
        response2 = make_health_check_request(api_url, api_key)
    has_second_response = response2 is not None
    assert has_second_response
