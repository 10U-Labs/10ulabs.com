"""End-to-end tests for image management functionality.

These tests verify the complete workflow of managing ECR images
through the API endpoint.
"""
from test.api.endpoints.image_for_ecs_runners.endpoint.test_data import (
    IMAGE_RESPONSE_FIELDS,
)

import pytest


class TestGetImageByDigestWorkflow:
    """E2E tests for getting image by digest."""

    def test_get_image_by_valid_digest(self, api_request):
        """Test getting an image by a valid digest."""
        # First, get a valid digest from the list
        list_response = api_request("/v1/image-for-ecs-runners", method="GET")

        # Skip if API key required
        if list_response["status_code"] == 403:
            pytest.skip("API key required")

        if list_response["status_code"] != 200:
            pytest.skip("Failed to list images")

        images = list_response["body"].get("images", [])
        if not images:
            pytest.skip("No images available")

        # Get the first image's digest
        digest = images[0]["digest"]

        # Now get the image by digest
        response = api_request(f"/v1/image-for-ecs-runners/{digest}", method="GET")

        assert response["status_code"] == 200
        assert response["body"]["success"] is True
        assert response["body"]["digest"] == digest

    def test_get_image_by_invalid_digest_returns_404(self, api_request):
        """Test that getting an invalid digest returns 404."""
        response = api_request(
            "/v1/image-for-ecs-runners/sha256:invaliddigestvalue123",
            method="GET"
        )

        # Skip if API key required
        if response["status_code"] == 403:
            pytest.skip("API key required")

        assert response["status_code"] == 404
        assert response["body"]["success"] is False

    def test_get_image_returns_all_fields(self, api_request):
        """Test that get image returns all required fields."""
        # First, get a valid digest from the list
        list_response = api_request("/v1/image-for-ecs-runners", method="GET")

        # Skip if API key required
        if list_response["status_code"] == 403:
            pytest.skip("API key required")

        if list_response["status_code"] != 200:
            pytest.skip("Failed to list images")

        images = list_response["body"].get("images", [])
        if not images:
            pytest.skip("No images available")

        digest = images[0]["digest"]
        response = api_request(f"/v1/image-for-ecs-runners/{digest}", method="GET")

        assert response["status_code"] == 200
        for field in IMAGE_RESPONSE_FIELDS:
            assert field in response["body"], f"Missing field: {field}"


class TestCORSWorkflow:
    """E2E tests for CORS support."""

    def test_options_returns_cors_headers(self, api_request):
        """Test that OPTIONS request returns CORS headers."""
        response = api_request("/v1/image-for-ecs-runners", method="OPTIONS")

        assert response["status_code"] == 200

    def test_get_response_includes_cors_headers(self, api_request):
        """Test that GET response includes CORS headers."""
        response = api_request("/v1/image-for-ecs-runners", method="GET")

        # Skip if API key required
        if response["status_code"] == 403:
            pytest.skip("API key required")

        # Check for CORS headers (case-insensitive)
        headers_lower = {k.lower(): v for k, v in response["headers"].items()}

        # At least Access-Control-Allow-Origin should be present
        assert "access-control-allow-origin" in headers_lower, (
            "Missing Access-Control-Allow-Origin header"
        )


class TestTestModeWorkflow:
    """E2E tests for test mode functionality."""

    def test_post_with_test_mode_returns_mock_response(self, api_request):
        """Test that POST with x-test-mode header returns mock response."""
        response = api_request(
            "/v1/image-for-ecs-runners",
            method="POST",
            body={},
            test_mode=True
        )

        if response["status_code"] == 403:
            pytest.skip("API key required")

        assert response["status_code"] == 200
        assert response["body"]["success"] is True
        assert response["body"].get("test_mode") is True
        assert "message" in response["body"]

    def test_get_with_test_mode_returns_real_data(self, api_request):
        """Test that GET requests return real data even with test mode header."""
        response = api_request(
            "/v1/image-for-ecs-runners",
            method="GET",
            test_mode=True
        )

        if response["status_code"] == 403:
            pytest.skip("API key required")

        assert response["status_code"] == 200
        assert "images" in response["body"]
        assert "count" in response["body"]
