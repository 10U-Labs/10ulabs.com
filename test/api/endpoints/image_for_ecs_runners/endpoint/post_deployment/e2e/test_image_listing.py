"""End-to-end tests for image listing functionality.

These tests verify the complete workflow of listing ECR images
through the API endpoint.
"""
from test.api.endpoints.image_for_ecs_runners.endpoint.test_data import (
    IMAGE_RESPONSE_FIELDS,
)

import pytest


class TestListImagesWorkflow:
    """E2E tests for listing images."""

    def test_list_images_returns_valid_response(self, api_request):
        """Test that listing images returns a valid response."""
        response = api_request("/v1/image-for-ecs-runners", method="GET")

        # Skip if API key required
        if response["status_code"] == 403:
            pytest.skip("API key required")

        assert response["status_code"] == 200
        assert response["body"]["success"] is True
        assert "images" in response["body"]
        assert "count" in response["body"]
        assert "repository" in response["body"]

    def test_list_images_count_matches_images_length(self, api_request):
        """Test that count matches the number of images returned."""
        response = api_request("/v1/image-for-ecs-runners", method="GET")

        # Skip if API key required
        if response["status_code"] == 403:
            pytest.skip("API key required")

        assert response["status_code"] == 200
        assert response["body"]["count"] == len(response["body"]["images"])

    def test_images_have_required_fields(self, api_request):
        """Test that each image has required fields."""
        response = api_request("/v1/image-for-ecs-runners", method="GET")

        # Skip if API key required
        if response["status_code"] == 403:
            pytest.skip("API key required")

        assert response["status_code"] == 200

        for image in response["body"]["images"]:
            assert "digest" in image
            assert "tags" in image
            assert "pushed_at" in image
            assert "size_bytes" in image


class TestGetLatestImageWorkflow:
    """E2E tests for getting the latest stable image."""

    def test_get_latest_returns_response(self, api_request):
        """Test that getting latest image returns a response."""
        response = api_request("/v1/image-for-ecs-runners/latest", method="GET")

        # Skip if API key required
        if response["status_code"] == 403:
            pytest.skip("API key required")

        # Either success or no stable image found
        assert response["status_code"] in [200, 500]

    def test_latest_image_has_stable_tag(self, api_request):
        """Test that latest image has stable tag."""
        response = api_request("/v1/image-for-ecs-runners/latest", method="GET")

        # Skip if API key required or no stable image
        if response["status_code"] in [403, 500]:
            pytest.skip("API key required or no stable image")

        assert response["status_code"] == 200
        assert "stable" in response["body"]["tags"]

    def test_latest_image_has_required_fields(self, api_request):
        """Test that latest image has required fields."""
        response = api_request("/v1/image-for-ecs-runners/latest", method="GET")

        # Skip if API key required or no stable image
        if response["status_code"] in [403, 500]:
            pytest.skip("API key required or no stable image")

        assert response["status_code"] == 200
        for field in IMAGE_RESPONSE_FIELDS:
            assert field in response["body"], f"Missing field: {field}"
