"""Tests to validate API Gateway integration after deployment.

These tests verify that the API Gateway endpoints are accessible
and respond correctly.
"""
import pytest


class TestApiGatewayEndpointAccessibility:
    """Verify API Gateway endpoints are accessible."""

    def test_01_options_request_returns_200(self, api_request):
        """Verify OPTIONS request returns 200 status."""
        response = api_request("/v1/image-for-ecs-runners", method="OPTIONS")

        assert response["status_code"] == 200

    def test_02_get_request_returns_200(self, api_request):
        """Verify GET request returns 200 status."""
        response = api_request("/v1/image-for-ecs-runners", method="GET")

        assert response["status_code"] == 200

    def test_03_get_latest_returns_valid_status(self, api_request):
        """Verify GET /latest returns 200 or 500 (no stable image)."""
        response = api_request("/v1/image-for-ecs-runners/latest", method="GET")

        assert response["status_code"] in [200, 500]


class TestApiGatewayResponseFormat:
    """Verify API Gateway response format."""

    @pytest.fixture
    def get_response(self, api_request):
        """Make GET request and return response."""
        return api_request("/v1/image-for-ecs-runners", method="GET")

    def test_01_get_returns_200(self, get_response):
        """Verify GET request returns 200 status."""
        assert get_response["status_code"] == 200

    def test_02_response_includes_content_type(self, get_response):
        """Verify response includes Content-Type header."""
        headers = get_response["headers"]

        assert "Content-Type" in headers or "content-type" in headers

    def test_03_response_body_is_dict(self, get_response):
        """Verify response body is a dict."""
        assert isinstance(get_response["body"], dict)

    def test_04_response_includes_success_field(self, get_response):
        """Verify response includes success field."""
        assert "success" in get_response["body"]


class TestApiGatewayErrorHandling:
    """Verify API Gateway error handling."""

    def test_01_unknown_path_returns_404(self, api_request):
        """Verify unknown path returns 404."""
        response = api_request("/v1/unknown-endpoint", method="GET")

        assert response["status_code"] == 404

    def test_02_invalid_digest_returns_404(self, api_request):
        """Verify invalid digest returns 404."""
        response = api_request(
            "/v1/image-for-ecs-runners/invalid-digest",
            method="GET"
        )

        assert response["status_code"] == 404
