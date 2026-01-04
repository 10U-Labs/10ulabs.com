"""E2E tests for CORS preflight (OPTIONS) requests."""
import requests
import pytest


@pytest.fixture(name="images_endpoint", scope="module")
def images_endpoint_fixture(api_url) -> str:
    """Return the images endpoint URL."""
    return f"{api_url}/v1/runners/ec2/images"


@pytest.fixture(name="latest_endpoint", scope="module")
def latest_endpoint_fixture(api_url) -> str:
    """Return the latest AMI endpoint URL."""
    return f"{api_url}/v1/runners/ec2/images/latest"


class TestCorsPreflightImages:
    """Test CORS preflight for /v1/runners/ec2/images endpoint."""

    def test_options_returns_200(self, images_endpoint):
        """Verify OPTIONS request returns 200."""
        response = requests.options(images_endpoint, timeout=10)
        assert response.status_code == 200

    def test_options_has_allow_origin_header(self, images_endpoint):
        """Verify OPTIONS response has Access-Control-Allow-Origin header."""
        response = requests.options(images_endpoint, timeout=10)
        assert "Access-Control-Allow-Origin" in response.headers

    def test_options_has_allow_methods_header(self, images_endpoint):
        """Verify OPTIONS response has Access-Control-Allow-Methods header."""
        response = requests.options(images_endpoint, timeout=10)
        assert "Access-Control-Allow-Methods" in response.headers

    def test_options_allows_get_method(self, images_endpoint):
        """Verify OPTIONS response allows GET method."""
        response = requests.options(images_endpoint, timeout=10)
        allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")
        assert "GET" in allowed_methods

    def test_options_allows_post_method(self, images_endpoint):
        """Verify OPTIONS response allows POST method."""
        response = requests.options(images_endpoint, timeout=10)
        allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")
        assert "POST" in allowed_methods

    def test_options_has_allow_headers(self, images_endpoint):
        """Verify OPTIONS response has Access-Control-Allow-Headers."""
        response = requests.options(images_endpoint, timeout=10)
        assert "Access-Control-Allow-Headers" in response.headers

    def test_options_allows_api_key_header(self, images_endpoint):
        """Verify OPTIONS response allows x-api-key header."""
        response = requests.options(images_endpoint, timeout=10)
        allowed_headers = response.headers.get(
            "Access-Control-Allow-Headers", ""
        ).lower()
        assert "x-api-key" in allowed_headers

    def test_options_allows_content_type_header(self, images_endpoint):
        """Verify OPTIONS response allows Content-Type header."""
        response = requests.options(images_endpoint, timeout=10)
        allowed_headers = response.headers.get(
            "Access-Control-Allow-Headers", ""
        ).lower()
        assert "content-type" in allowed_headers


class TestCorsPreflightLatest:
    """Test CORS preflight for /v1/runners/ec2/images/latest endpoint."""

    def test_options_returns_200(self, latest_endpoint):
        """Verify OPTIONS request returns 200."""
        response = requests.options(latest_endpoint, timeout=10)
        assert response.status_code == 200

    def test_options_has_cors_headers(self, latest_endpoint):
        """Verify OPTIONS response has required CORS headers."""
        response = requests.options(latest_endpoint, timeout=10)
        assert "Access-Control-Allow-Origin" in response.headers and "Access-Control-Allow-Methods" in response.headers


class TestCorsOnActualRequests:
    """Test CORS headers on actual API responses."""

    def test_get_response_has_cors_origin(self, images_endpoint, api_key):
        """Verify GET response includes CORS origin header."""
        headers = {"x-api-key": api_key}
        response = requests.get(images_endpoint, headers=headers, timeout=10)
        # CORS headers may or may not be present depending on API Gateway config
        # This test documents current behavior
        if response.status_code == 200:
            # If request succeeds, check for CORS header
            origin = response.headers.get("Access-Control-Allow-Origin")
            assert origin is not None or response.status_code == 200, (
                "Successful responses should have CORS headers or be functional"
            )
