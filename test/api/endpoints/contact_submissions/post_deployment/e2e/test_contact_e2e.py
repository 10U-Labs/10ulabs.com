"""End-to-end tests for contact endpoint.

E2E tests verify critical user journeys that cannot be caught by unit or
integration tests. They run against the deployed API and use test mode
to avoid side effects.

These tests answer: "Does the user journey work?"
"""

import time

import requests


TEST_HEADERS = {"x-test-mode": "true", "Content-Type": "application/json"}


def create_contact_payload():
    """Create a valid contact form payload for testing."""
    return {
        "name": "E2E Test User",
        "email": "e2e-test@example.com",
        "message": "This is an e2e test message.",
        "recaptcha_token": "e2e-test-token"
    }


class TestContactFormSubmission:
    """
    User Journey: Contact form submission via website.

    When: A user fills out and submits the contact form
    Then: The form is processed and a success response is returned

    Critical Path: HTTP -> API Gateway -> Lambda -> (test mode bypass)
    Failure Impact: Users cannot contact the company
    """

    def test_contact_form_submission_returns_success(self, api_url):
        """Verify contact form submission returns success in test mode."""
        payload = create_contact_payload()
        response = requests.post(
            f"{api_url}/v1/contact-submissions",
            headers=TEST_HEADERS, json=payload, timeout=10
        )
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    def test_contact_form_submission_returns_json(self, api_url):
        """Verify contact form returns JSON content type."""
        payload = create_contact_payload()
        response = requests.post(
            f"{api_url}/v1/contact-submissions",
            headers=TEST_HEADERS, json=payload, timeout=10
        )
        content_type = response.headers.get("Content-Type", "")
        assert content_type.startswith("application/json"), (
            f"Expected JSON content type, got: {content_type}"
        )

    def test_contact_form_submission_confirms_test_mode(self, api_url):
        """Verify test mode flag is returned in response."""
        payload = create_contact_payload()
        response = requests.post(
            f"{api_url}/v1/contact-submissions",
            headers=TEST_HEADERS, json=payload, timeout=10
        )
        body = response.json()
        assert body.get("test_mode") is True, (
            "Expected test_mode=true in response"
        )


class TestContactEndpointCORS:
    """
    User Journey: Browser preflight request for contact form.

    When: A browser sends an OPTIONS request before the form submission
    Then: CORS headers are returned allowing the request

    Critical Path: HTTP -> API Gateway -> Lambda (OPTIONS handler)
    Failure Impact: Form cannot be submitted from web browsers
    """

    def test_options_request_returns_200(self, api_url):
        """Verify OPTIONS request returns 200."""
        response = requests.options(f"{api_url}/v1/contact-submissions", timeout=10)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}"
        )

    def test_cors_header_present_in_response(self, api_url):
        """Verify CORS Allow-Origin header is present."""
        payload = create_contact_payload()
        response = requests.post(
            f"{api_url}/v1/contact-submissions",
            headers=TEST_HEADERS, json=payload, timeout=10
        )
        assert "Access-Control-Allow-Origin" in response.headers, (
            "Missing CORS Access-Control-Allow-Origin header"
        )


class TestContactEndpointPerformance:
    """
    User Journey: Fast form submission response.

    When: A user submits the contact form
    Then: They receive a response within acceptable time limits

    Critical Path: Full request/response cycle
    Failure Impact: Poor user experience, potential timeout errors
    """

    def test_response_time_under_5_seconds(self, api_url):
        """Verify response time is under 5 seconds."""
        payload = create_contact_payload()
        start = time.time()
        requests.post(
            f"{api_url}/v1/contact-submissions",
            headers=TEST_HEADERS, json=payload, timeout=10
        )
        elapsed = time.time() - start
        assert elapsed < 5.0, (
            f"Response time {elapsed:.2f}s exceeds 5 second limit"
        )

    def test_stable_over_multiple_requests(self, api_url):
        """Verify endpoint is stable over multiple sequential requests."""
        payload = create_contact_payload()
        statuses = []
        for _ in range(3):
            response = requests.post(
                f"{api_url}/v1/contact-submissions",
                headers=TEST_HEADERS, json=payload, timeout=10
            )
            statuses.append(response.status_code)
        assert all(s == 200 for s in statuses), (
            f"Unstable responses: {statuses}"
        )


class TestContactEndpointValidation:
    """
    User Journey: Form validation feedback.

    When: A user submits an invalid form
    Then: They receive a clear error response

    Critical Path: HTTP -> API Gateway -> Lambda (validation)
    Failure Impact: Poor user experience, unclear errors
    """

    def test_missing_name_returns_400(self, api_url):
        """Verify missing name returns 400 error."""
        payload = create_contact_payload()
        payload["name"] = ""
        response = requests.post(
            f"{api_url}/v1/contact-submissions",
            headers=TEST_HEADERS, json=payload, timeout=10
        )
        assert response.status_code == 400, (
            f"Expected 400 for missing name, got {response.status_code}"
        )

    def test_invalid_email_returns_400(self, api_url):
        """Verify invalid email returns 400 error."""
        payload = create_contact_payload()
        payload["email"] = "not-an-email"
        response = requests.post(
            f"{api_url}/v1/contact-submissions",
            headers=TEST_HEADERS, json=payload, timeout=10
        )
        assert response.status_code == 400, (
            f"Expected 400 for invalid email, got {response.status_code}"
        )
