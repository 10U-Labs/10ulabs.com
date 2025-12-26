"""End-to-end tests for image management functionality.

These tests verify the complete workflow of managing ECR images
through the API endpoint.
"""
import pytest


class TestGetImageByDigestWorkflow:
    """E2E tests for getting image by digest."""

    @pytest.fixture
    def first_digest(self, api_request):
        """Get first image digest from list response."""
        response = api_request("/v1/runners/ecs/images", method="GET")
        if response["status_code"] != 200:
            pytest.fail(f"List images failed: {response['status_code']}")
        images = response["body"].get("images", [])
        if not images:
            pytest.skip("No images available in repository")
        return images[0]["digest"]

    @pytest.fixture
    def digest_response(self, api_request, first_digest):
        """Get image by digest response."""
        return api_request(f"/v1/runners/ecs/images/{first_digest}", method="GET")

    def test_01_get_by_digest_returns_200(self, digest_response):
        """Verify get by digest returns 200."""
        assert digest_response["status_code"] == 200

    def test_02_get_by_digest_success_is_true(self, digest_response):
        """Verify get by digest success is True."""
        assert digest_response["body"]["success"] is True

    def test_03_get_by_digest_returns_correct_digest(self, digest_response, first_digest):
        """Verify returned digest matches requested digest."""
        assert digest_response["body"]["digest"] == first_digest

    def test_04_get_by_digest_has_tags(self, digest_response):
        """Verify get by digest has tags field."""
        assert "tags" in digest_response["body"]

    def test_05_get_by_digest_has_pushed_at(self, digest_response):
        """Verify get by digest has pushed_at field."""
        assert "pushed_at" in digest_response["body"]

    def test_06_get_by_digest_has_size_bytes(self, digest_response):
        """Verify get by digest has size_bytes field."""
        assert "size_bytes" in digest_response["body"]


class TestGetImageByInvalidDigest:
    """Tests for getting image with invalid digest."""

    @pytest.fixture
    def invalid_response(self, api_request):
        """Get response for invalid digest request."""
        return api_request(
            "/v1/runners/ecs/images/sha256:invaliddigestvalue123",
            method="GET"
        )

    def test_01_returns_404(self, invalid_response):
        """Verify invalid digest returns 404."""
        assert invalid_response["status_code"] == 404

    def test_02_success_is_false(self, invalid_response):
        """Verify success is False for invalid digest."""
        assert invalid_response["body"]["success"] is False


class TestCORSWorkflow:
    """E2E tests for CORS support."""

    def test_01_options_returns_200(self, api_request):
        """Verify OPTIONS request returns 200."""
        response = api_request("/v1/runners/ecs/images", method="OPTIONS")

        assert response["status_code"] == 200

    @pytest.fixture
    def get_response(self, api_request):
        """Make GET request and return response."""
        return api_request("/v1/runners/ecs/images", method="GET")

    def test_02_get_returns_200(self, get_response):
        """Verify GET request returns 200."""
        assert get_response["status_code"] == 200

    def test_03_get_has_cors_header(self, get_response):
        """Verify GET response has CORS header."""
        headers_lower = {k.lower(): v for k, v in get_response["headers"].items()}

        assert "access-control-allow-origin" in headers_lower


class TestTestModeWorkflow:
    """E2E tests for test mode functionality."""

    @pytest.fixture
    def test_mode_post_response(self, api_request):
        """Make POST request with test mode and return response."""
        return api_request(
            "/v1/runners/ecs/images",
            method="POST",
            body={},
            test_mode=True
        )

    def test_01_post_test_mode_returns_200(self, test_mode_post_response):
        """Verify POST with test mode returns 200."""
        assert test_mode_post_response["status_code"] == 200

    def test_02_post_test_mode_success_is_true(self, test_mode_post_response):
        """Verify POST with test mode success is True."""
        assert test_mode_post_response["body"]["success"] is True

    def test_03_post_test_mode_flag_is_true(self, test_mode_post_response):
        """Verify POST response has test_mode flag True."""
        assert test_mode_post_response["body"].get("test_mode") is True

    def test_04_post_test_mode_has_message(self, test_mode_post_response):
        """Verify POST with test mode has message field."""
        assert "message" in test_mode_post_response["body"]

    @pytest.fixture
    def test_mode_get_response(self, api_request):
        """Make GET request with test mode and return response."""
        return api_request(
            "/v1/runners/ecs/images",
            method="GET",
            test_mode=True
        )

    def test_05_get_test_mode_returns_200(self, test_mode_get_response):
        """Verify GET with test mode returns 200."""
        assert test_mode_get_response["status_code"] == 200

    def test_06_get_test_mode_has_images(self, test_mode_get_response):
        """Verify GET with test mode has images field."""
        assert "images" in test_mode_get_response["body"]

    def test_07_get_test_mode_has_count(self, test_mode_get_response):
        """Verify GET with test mode has count field."""
        assert "count" in test_mode_get_response["body"]
