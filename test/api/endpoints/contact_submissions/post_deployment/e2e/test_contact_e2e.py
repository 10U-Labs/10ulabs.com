import time
from typing import Any, Dict

import requests


TEST_HEADERS = {"x-test-mode": "true", "Content-Type": "application/json"}


def create_contact_payload() -> Dict[str, Any]:
    return {
        "name": "E2E Test User",
        "email": "e2e-test@example.com",
        "message": "This is an e2e test message.",
        "recaptcha_token": "e2e-test-token"
    }


class TestContactFormSubmission:
    def test_contact_form_submission_returns_success(self, api_url: str) -> None:
        payload = create_contact_payload()
        response = requests.post(
            f"{api_url}/v1/contact-submissions",
            headers=TEST_HEADERS, json=payload, timeout=10
        )
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    def test_contact_form_submission_returns_json(self, api_url: str) -> None:
        payload = create_contact_payload()
        response = requests.post(
            f"{api_url}/v1/contact-submissions",
            headers=TEST_HEADERS, json=payload, timeout=10
        )
        content_type = response.headers.get("Content-Type", "")
        assert content_type.startswith("application/json"), (
            f"Expected JSON content type, got: {content_type}"
        )

    def test_contact_form_submission_confirms_test_mode(self, api_url: str) -> None:
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
    def test_options_request_returns_200(self, api_url: str) -> None:
        response = requests.options(f"{api_url}/v1/contact-submissions", timeout=10)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}"
        )

    def test_cors_header_present_in_response(self, api_url: str) -> None:
        payload = create_contact_payload()
        response = requests.post(
            f"{api_url}/v1/contact-submissions",
            headers=TEST_HEADERS, json=payload, timeout=10
        )
        assert "Access-Control-Allow-Origin" in response.headers, (
            "Missing CORS Access-Control-Allow-Origin header"
        )


class TestContactEndpointPerformance:
    def test_response_time_under_5_seconds(self, api_url: str) -> None:
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

    def test_stable_over_multiple_requests(self, api_url: str) -> None:
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
    def test_missing_name_returns_400(self, api_url: str) -> None:
        payload = create_contact_payload()
        payload["name"] = ""
        response = requests.post(
            f"{api_url}/v1/contact-submissions",
            headers=TEST_HEADERS, json=payload, timeout=10
        )
        assert response.status_code == 400, (
            f"Expected 400 for missing name, got {response.status_code}"
        )

    def test_invalid_email_returns_400(self, api_url: str) -> None:
        payload = create_contact_payload()
        payload["email"] = "not-an-email"
        response = requests.post(
            f"{api_url}/v1/contact-submissions",
            headers=TEST_HEADERS, json=payload, timeout=10
        )
        assert response.status_code == 400, (
            f"Expected 400 for invalid email, got {response.status_code}"
        )
