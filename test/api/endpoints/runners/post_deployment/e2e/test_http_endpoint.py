"""E2E tests for /v1/runners HTTP endpoint.

User Journey: HTTP POST to /v1/runners → API Gateway → SQS → Lambda routing

Critical Path: HTTP request → API Gateway authentication → SQS queue
Failure Impact: Runner requests not queued, GitHub Actions jobs not processed.
"""
import requests

import pytest

from .conftest import create_runner_request, make_authenticated_post


class TestRunnersPostAuthentication:
    """Test POST /v1/runners authentication requirements."""

    def test_post_without_api_key_returns_403(self, runners_endpoint):
        """Verify POST without API key returns 403 Forbidden.

        User Journey: Unauthenticated request to queue runner

        When: A POST request without API key is sent to /v1/runners
        Then: The request is rejected with 403 Forbidden
        """
        payload = create_runner_request("ec2", job_id=88888)
        response = requests.post(runners_endpoint, json=payload, timeout=10)
        assert response.status_code == 403

    def test_post_with_invalid_api_key_returns_403(self, runners_endpoint):
        """Verify POST with invalid API key returns 403 Forbidden.

        User Journey: Request with wrong credentials

        When: A POST request with invalid API key is sent to /v1/runners
        Then: The request is rejected with 403 Forbidden
        """
        payload = create_runner_request("ec2", job_id=88889)
        headers = {"x-api-key": "invalid-key-12345"}
        response = requests.post(
            runners_endpoint, json=payload, headers=headers, timeout=10
        )
        assert response.status_code == 403


class TestRunnersPostSuccess:
    """Test POST /v1/runners successful requests."""

    def test_post_with_valid_api_key_returns_200(self, runners_endpoint, api_key):
        """Verify POST with valid API key returns 200.

        User Journey: Authenticated request to queue runner

        When: A POST request with valid API key is sent to /v1/runners
        Then: The request succeeds with 200 OK
        """
        payload = create_runner_request("ec2", job_id=77777)
        response = make_authenticated_post(
            runners_endpoint, api_key, json=payload, timeout=10
        )
        assert response.status_code == 200

    def test_post_response_has_json_content_type(self, runners_endpoint, api_key):
        """Verify POST response has JSON content type.

        User Journey: API response format verification

        When: A POST request is sent to /v1/runners
        Then: The response has Content-Type: application/json
        """
        payload = create_runner_request("ec2", job_id=77778)
        response = make_authenticated_post(
            runners_endpoint, api_key, json=payload, timeout=10
        )
        content_type = response.headers.get("Content-Type", "")
        assert "application/json" in content_type

    def test_post_response_has_message_id(self, runners_endpoint, api_key):
        """Verify POST response contains SQS message ID.

        User Journey: Verify message was queued

        When: A POST request is sent to /v1/runners
        Then: The response contains a MessageId indicating SQS accepted the message
        """
        payload = create_runner_request("ec2", job_id=77779)
        response = make_authenticated_post(
            runners_endpoint, api_key, json=payload, timeout=10
        )
        body = response.json()
        assert "MessageId" in body or "messageId" in body


class TestRunnersPostValidation:
    """Test POST /v1/runners request validation."""

    def test_post_with_ec2_labels_accepted(self, runners_endpoint, api_key):
        """Verify POST with EC2 labels is accepted.

        User Journey: Queue EC2 runner request

        When: A POST with EC2 labels is sent to /v1/runners
        Then: The request is accepted (200)
        """
        payload = create_runner_request("ec2", job_id=66661)
        response = make_authenticated_post(
            runners_endpoint, api_key, json=payload, timeout=10
        )
        assert response.status_code == 200

    def test_post_with_ecs_labels_accepted(self, runners_endpoint, api_key):
        """Verify POST with ECS labels is accepted.

        User Journey: Queue ECS runner request

        When: A POST with ECS/Fargate labels is sent to /v1/runners
        Then: The request is accepted (200)
        """
        payload = create_runner_request("ecs", job_id=66662)
        response = make_authenticated_post(
            runners_endpoint, api_key, json=payload, timeout=10
        )
        assert response.status_code == 200

    def test_post_with_unknown_labels_accepted(self, runners_endpoint, api_key):
        """Verify POST with unknown labels is still accepted by API Gateway.

        User Journey: Queue runner request with non-matching labels

        When: A POST with labels that don't match ec2/ecs is sent
        Then: API Gateway still accepts (routing happens in Lambda)
        """
        payload = {
            "job_id": 66663,
            "job_labels": ["self-hosted", "macos", "arm64"],
            "github_repo": "test/repo",
            "run_id": 99999
        }
        response = make_authenticated_post(
            runners_endpoint, api_key, json=payload, timeout=10
        )
        assert response.status_code == 200


class TestRunnersOptionsCors:
    """Test OPTIONS /v1/runners CORS preflight."""

    def test_options_returns_200(self, runners_endpoint):
        """Verify OPTIONS request returns 200.

        User Journey: Browser CORS preflight check

        When: An OPTIONS request is sent to /v1/runners
        Then: The request succeeds with 200 OK
        """
        response = requests.options(runners_endpoint, timeout=10)
        assert response.status_code == 200

    def test_options_has_allow_origin_header(self, runners_endpoint):
        """Verify OPTIONS response has Access-Control-Allow-Origin header.

        User Journey: CORS origin verification

        When: An OPTIONS request is sent to /v1/runners
        Then: The response has Access-Control-Allow-Origin header
        """
        response = requests.options(runners_endpoint, timeout=10)
        assert "Access-Control-Allow-Origin" in response.headers

    def test_options_has_allow_methods_header(self, runners_endpoint):
        """Verify OPTIONS response has Access-Control-Allow-Methods header.

        User Journey: CORS methods verification

        When: An OPTIONS request is sent to /v1/runners
        Then: The response has Access-Control-Allow-Methods header
        """
        response = requests.options(runners_endpoint, timeout=10)
        assert "Access-Control-Allow-Methods" in response.headers

    def test_options_allows_post_method(self, runners_endpoint):
        """Verify OPTIONS response allows POST method.

        User Journey: Verify POST is allowed by CORS

        When: An OPTIONS request is sent to /v1/runners
        Then: POST is listed in Access-Control-Allow-Methods
        """
        response = requests.options(runners_endpoint, timeout=10)
        allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")
        assert "POST" in allowed_methods

    def test_options_has_allow_headers(self, runners_endpoint):
        """Verify OPTIONS response has Access-Control-Allow-Headers.

        User Journey: CORS headers verification

        When: An OPTIONS request is sent to /v1/runners
        Then: The response has Access-Control-Allow-Headers header
        """
        response = requests.options(runners_endpoint, timeout=10)
        assert "Access-Control-Allow-Headers" in response.headers

    def test_options_allows_api_key_header(self, runners_endpoint):
        """Verify OPTIONS response allows x-api-key header.

        User Journey: Verify API key header is allowed by CORS

        When: An OPTIONS request is sent to /v1/runners
        Then: x-api-key is listed in Access-Control-Allow-Headers
        """
        response = requests.options(runners_endpoint, timeout=10)
        allowed_headers = response.headers.get(
            "Access-Control-Allow-Headers", ""
        ).lower()
        assert "x-api-key" in allowed_headers

    def test_options_allows_content_type_header(self, runners_endpoint):
        """Verify OPTIONS response allows Content-Type header.

        User Journey: Verify Content-Type header is allowed by CORS

        When: An OPTIONS request is sent to /v1/runners
        Then: Content-Type is listed in Access-Control-Allow-Headers
        """
        response = requests.options(runners_endpoint, timeout=10)
        allowed_headers = response.headers.get(
            "Access-Control-Allow-Headers", ""
        ).lower()
        assert "content-type" in allowed_headers
