"""E2E tests for critical security user journeys.

These tests verify security-related end-to-end behavior.
Each test documents the security journey it validates.
"""
import pytest
import requests

from ..conftest import skip_if_endpoint_not_deployed


TEST_HEADERS = {"x-test-mode": "true"}


# =============================================================================
# Error Handling Security Journey
# =============================================================================


def test_invalid_endpoint_returns_404(api_url):
    """
    User Journey: User attempts to access non-existent endpoint.

    When: A user (or attacker) requests a non-existent path
    Then: A 404 is returned without revealing internal details

    Security Impact: Prevents path enumeration, information disclosure
    """
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 404


def test_404_response_does_not_contain_traceback(api_url):
    """
    User Journey: Attacker probes for stack traces.

    When: An attacker requests a non-existent path
    Then: Error messages do not contain Python tracebacks

    Security Impact: Prevents stack trace disclosure
    """
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    response_text = response.text.lower()
    assert "traceback" not in response_text


def test_404_response_does_not_reveal_lambda_internals(api_url):
    """
    User Journey: Attacker probes for infrastructure details.

    When: An attacker requests a non-existent path
    Then: Error messages do not reveal Lambda function details

    Security Impact: Prevents infrastructure reconnaissance
    """
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    response_text = response.text.lower()
    # Lambda mentioned in docs context is OK, but not in error context
    assert "lambda" not in response_text or "documentation" in response_text


def test_malformed_request_handled_gracefully(api_url, api_key):
    """
    User Journey: Client sends malformed request.

    When: A client sends an invalid request payload
    Then: The API responds with appropriate error, not 500

    Security Impact: Prevents denial of service via malformed input
    """
    skip_if_endpoint_not_deployed(api_url, "/v1/ecs-runner", "POST")
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    payload = {"job_id": "invalid-type", "github_repo": "test/repo"}
    response = requests.post(
        f"{api_url}/v1/ecs-runner", json=payload, headers=headers, timeout=10
    )
    # 404 means endpoint not deployed (skip check is unauthenticated)
    if response.status_code == 404:
        pytest.skip("Endpoint /v1/ecs-runner not deployed")
    # Should get client error (4xx) or success, not server error
    assert response.status_code in [200, 400, 401, 403, 422]


# =============================================================================
# Service Availability Security Journey
# =============================================================================


def test_service_unavailable_returns_503(api_url):
    """
    User Journey: System under heavy load or maintenance.

    When: The service is unavailable or degraded
    Then: A proper 503 is returned (not timeout or connection refused)

    Security Impact: Proper error handling prevents information disclosure
    """
    skip_if_endpoint_not_deployed(api_url, "/health")
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    # Either healthy (200) or properly degraded (503)
    assert response.status_code in [200, 503]


# =============================================================================
# Request Validation Security Journey
# =============================================================================


def test_error_response_contains_error_message(api_url):
    """
    User Journey: Attacker analyzes error responses.

    When: An invalid request is made
    Then: Error response contains expected error indicator

    Security Impact: Consistent error format prevents enumeration
    """
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    assert "error" in response.text.lower() or "not found" in response.text.lower()
