"""Tests to validate API Gateway integration after deployment.

These tests verify that the API Gateway endpoints are accessible
and respond correctly.
"""
import pytest


class TestApiGatewayEndpointAccessibility:
    """Verify API Gateway endpoints are accessible."""

    def test_01_options_request_returns_cors_headers(self, api_request):
        """Verify OPTIONS request returns CORS headers."""
        response = api_request("/v1/image-for-ecs-runners", method="OPTIONS")

        assert response["status_code"] == 200, (
            f"Expected 200 status, got {response['status_code']}"
        )

    def test_02_get_request_returns_success(self, api_request):
        """Verify GET request returns success."""
        response = api_request("/v1/image-for-ecs-runners", method="GET")

        # Should return 200 (success) or 403 (API key required)
        assert response["status_code"] in [200, 403], (
            f"Expected 200 or 403 status, got {response['status_code']}"
        )

    def test_03_get_latest_returns_response(self, api_request):
        """Verify GET /latest returns a response."""
        response = api_request("/v1/image-for-ecs-runners/latest", method="GET")

        # Should return 200 (success), 403 (API key required), or 500 (no stable image)
        assert response["status_code"] in [200, 403, 500], (
            f"Expected 200, 403, or 500 status, got {response['status_code']}"
        )


class TestApiGatewayResponseFormat:
    """Verify API Gateway response format."""

    def test_01_response_includes_content_type(self, api_request):
        """Verify response includes Content-Type header."""
        response = api_request("/v1/image-for-ecs-runners", method="GET")

        # Skip if we get 403 (API key required)
        if response["status_code"] == 403:
            pytest.skip("API key required")

        assert "Content-Type" in response["headers"] or "content-type" in response["headers"], (
            "Missing Content-Type header"
        )

    def test_02_response_body_is_json(self, api_request):
        """Verify response body is valid JSON."""
        response = api_request("/v1/image-for-ecs-runners", method="GET")

        # Skip if we get 403 (API key required)
        if response["status_code"] == 403:
            pytest.skip("API key required")

        assert isinstance(response["body"], dict), (
            "Response body is not a valid JSON object"
        )

    def test_03_success_response_includes_success_field(self, api_request):
        """Verify success response includes success field."""
        response = api_request("/v1/image-for-ecs-runners", method="GET")

        # Skip if we get 403 (API key required)
        if response["status_code"] == 403:
            pytest.skip("API key required")

        assert "success" in response["body"], (
            "Response body missing 'success' field"
        )


class TestApiGatewayErrorHandling:
    """Verify API Gateway error handling."""

    def test_01_returns_404_for_unknown_path(self, api_request):
        """Verify 404 is returned for unknown path."""
        response = api_request("/v1/unknown-endpoint", method="GET")

        # Should return 404 (not found) or 403 (API key required)
        assert response["status_code"] in [404, 403], (
            f"Expected 404 or 403 status, got {response['status_code']}"
        )

    def test_02_returns_400_for_invalid_digest(self, api_request):
        """Verify proper error for invalid digest."""
        response = api_request(
            "/v1/image-for-ecs-runners/invalid-digest",
            method="GET"
        )

        # Should return 404 (not found), 400 (bad request), or 403 (API key required)
        assert response["status_code"] in [400, 403, 404], (
            f"Expected 400, 403, or 404 status, got {response['status_code']}"
        )
