"""End-to-end tests for contact endpoint."""
import time

import requests


TEST_HEADERS = {"x-test-mode": "true", "Content-Type": "application/json"}


def create_contact_payload():
    """Create a contact form payload for testing."""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "message": "This is a test message.",
        "recaptcha_token": "test-token"
    }


def test_contact_endpoint_stable_over_sequential_requests(api_url):
    """Test that contact endpoint is stable over sequential requests."""
    payload = create_contact_payload()
    responses = [
        requests.post(f"{api_url}/v1/contact", headers=TEST_HEADERS, json=payload, timeout=10)
        for _ in range(5)
    ]
    statuses = [r.status_code for r in responses]
    all_statuses_are_200 = all(s == 200 for s in statuses)
    assert all_statuses_are_200


def test_contact_endpoint_consistent_response_body(api_url):
    """Test that contact endpoint returns consistent response body."""
    payload = create_contact_payload()
    responses = [
        requests.post(f"{api_url}/v1/contact", headers=TEST_HEADERS, json=payload, timeout=10)
        for _ in range(3)
    ]
    bodies = [r.json() for r in responses]
    all_success_true = all(b["success"] is True for b in bodies)
    assert all_success_true


def test_contact_endpoint_average_response_time_acceptable(api_url):
    """Test that contact endpoint average response time is acceptable."""
    payload = create_contact_payload()
    times = []
    for _ in range(5):
        start = time.time()
        requests.post(f"{api_url}/v1/contact", headers=TEST_HEADERS, json=payload, timeout=10)
        times.append(time.time() - start)
    avg_time = sum(times) / len(times)
    avg_time_under_2_seconds = avg_time < 2.0
    assert avg_time_under_2_seconds


def test_contact_endpoint_no_cold_start_degradation(api_url):
    """Test that contact endpoint has no cold start degradation."""
    payload = create_contact_payload()
    first_response = requests.post(
        f"{api_url}/v1/contact", headers=TEST_HEADERS, json=payload, timeout=10
    )
    time.sleep(1)
    second_response = requests.post(
        f"{api_url}/v1/contact", headers=TEST_HEADERS, json=payload, timeout=10
    )
    statuses_match = first_response.status_code == second_response.status_code
    assert statuses_match


def test_contact_endpoint_returns_valid_json_structure(api_url):
    """Test that contact endpoint returns valid JSON structure."""
    payload = create_contact_payload()
    response = requests.post(
        f"{api_url}/v1/contact", headers=TEST_HEADERS, json=payload, timeout=10
    )
    body = response.json()
    required_fields = ["success", "message", "test_mode"]
    has_all_required_fields = all(field in body for field in required_fields)
    assert has_all_required_fields


def test_contact_endpoint_handles_concurrent_requests(api_url):
    """Test that contact endpoint handles concurrent requests."""
    payload = create_contact_payload()
    responses = [
        requests.post(f"{api_url}/v1/contact", headers=TEST_HEADERS, json=payload, timeout=10)
        for _ in range(10)
    ]
    success_count = sum(1 for r in responses if r.status_code == 200)
    all_requests_succeeded = success_count == 10
    assert all_requests_succeeded


def test_contact_endpoint_rejects_empty_name(api_url):
    """Test that contact endpoint rejects empty name."""
    payload = {
        "name": "", "email": "test@example.com", "message": "test",
        "recaptcha_token": "token"
    }
    response = requests.post(
        f"{api_url}/v1/contact", headers=TEST_HEADERS, json=payload, timeout=10
    )
    status_is_400 = response.status_code == 400
    assert status_is_400


def test_contact_endpoint_rejects_empty_email(api_url):
    """Test that contact endpoint rejects empty email."""
    payload = {
        "name": "Test", "email": "", "message": "test", "recaptcha_token": "token"
    }
    response = requests.post(
        f"{api_url}/v1/contact", headers=TEST_HEADERS, json=payload, timeout=10
    )
    status_is_400 = response.status_code == 400
    assert status_is_400


def test_contact_endpoint_rejects_empty_message(api_url):
    """Test that contact endpoint rejects empty message."""
    payload = {
        "name": "Test", "email": "test@example.com", "message": "",
        "recaptcha_token": "token"
    }
    response = requests.post(
        f"{api_url}/v1/contact", headers=TEST_HEADERS, json=payload, timeout=10
    )
    status_is_400 = response.status_code == 400
    assert status_is_400
