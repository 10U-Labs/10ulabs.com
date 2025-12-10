"""End-to-end tests for image listing functionality.

These tests verify the complete workflow of listing ECR images
through the API endpoint.
"""
import pytest


class TestListImagesWorkflow:
    """E2E tests for listing images."""

    @pytest.fixture
    def list_response(self, api_request):
        """Make list images request and return response."""
        return api_request("/v1/image-for-ecs-runners", method="GET")

    def test_01_returns_200(self, list_response):
        """Verify list images returns 200 status."""
        assert list_response["status_code"] == 200

    def test_02_success_is_true(self, list_response):
        """Verify success field is True."""
        assert list_response["body"]["success"] is True

    def test_03_has_images_field(self, list_response):
        """Verify response has images field."""
        assert "images" in list_response["body"]

    def test_04_has_count_field(self, list_response):
        """Verify response has count field."""
        assert "count" in list_response["body"]

    def test_05_has_repository_field(self, list_response):
        """Verify response has repository field."""
        assert "repository" in list_response["body"]

    def test_06_count_matches_images_length(self, list_response):
        """Verify count matches number of images."""
        assert list_response["body"]["count"] == len(list_response["body"]["images"])


class TestImageFields:
    """Verify each image has required fields."""

    @pytest.fixture
    def first_image(self, api_request):
        """Get first image from list response."""
        response = api_request("/v1/image-for-ecs-runners", method="GET")
        images = response["body"].get("images", [])
        if not images:
            pytest.skip("No images in repository")
        return images[0]

    def test_01_image_has_digest(self, first_image):
        """Verify image has digest field."""
        assert "digest" in first_image

    def test_02_image_has_tags(self, first_image):
        """Verify image has tags field."""
        assert "tags" in first_image

    def test_03_image_has_pushed_at(self, first_image):
        """Verify image has pushed_at field."""
        assert "pushed_at" in first_image

    def test_04_image_has_size_bytes(self, first_image):
        """Verify image has size_bytes field."""
        assert "size_bytes" in first_image


class TestGetLatestImageWorkflow:
    """E2E tests for getting the latest stable image."""

    @pytest.fixture
    def latest_response(self, api_request):
        """Make get latest request and return response."""
        return api_request("/v1/image-for-ecs-runners/latest", method="GET")

    def test_01_returns_valid_status(self, latest_response):
        """Verify latest returns 200 or 500."""
        assert latest_response["status_code"] in [200, 500]


class TestLatestImageSuccess:
    """Tests for when a stable image exists."""

    @pytest.fixture
    def latest_response(self, api_request):
        """Get latest image response, skip if no stable image."""
        response = api_request("/v1/image-for-ecs-runners/latest", method="GET")
        if response["status_code"] == 500:
            pytest.skip("No stable image available")
        return response

    def test_01_returns_200(self, latest_response):
        """Verify latest returns 200 when stable image exists."""
        assert latest_response["status_code"] == 200

    def test_02_has_stable_tag(self, latest_response):
        """Verify latest image has stable tag."""
        assert "stable" in latest_response["body"]["tags"]

    def test_03_has_digest_field(self, latest_response):
        """Verify latest image has digest field."""
        assert "digest" in latest_response["body"]

    def test_04_has_tags_field(self, latest_response):
        """Verify latest image has tags field."""
        assert "tags" in latest_response["body"]

    def test_05_has_pushed_at_field(self, latest_response):
        """Verify latest image has pushed_at field."""
        assert "pushed_at" in latest_response["body"]

    def test_06_has_size_bytes_field(self, latest_response):
        """Verify latest image has size_bytes field."""
        assert "size_bytes" in latest_response["body"]


class TestLatestImageNoStable:
    """Tests for when no stable image exists."""

    @pytest.fixture
    def error_response(self, api_request):
        """Get latest image response, skip if stable image exists."""
        response = api_request("/v1/image-for-ecs-runners/latest", method="GET")
        if response["status_code"] == 200:
            pytest.skip("Stable image exists")
        return response

    def test_01_returns_500(self, error_response):
        """Verify returns 500 when no stable image."""
        assert error_response["status_code"] == 500

    def test_02_error_message_correct(self, error_response):
        """Verify error message mentions no stable image."""
        assert "No stable image found" in error_response["body"].get("error", "")
