"""Unit tests for health check Lambda.

Tests follow atomic principle - one assertion per test.
"""
import json


class TestHealthCheckGetMethod:
    """Tests for GET /v1/runners/health."""

    def test_01_returns_200_status(self, health_check_module, lambda_context):
        """Test health check returns 200 for GET."""
        event = {"httpMethod": "GET", "path": "/v1/runners/health"}
        response = health_check_module.lambda_handler(event, lambda_context)
        assert response["statusCode"] == 200

    def test_02_returns_json_content_type(self, health_check_module, lambda_context):
        """Test health check returns JSON content type."""
        event = {"httpMethod": "GET", "path": "/v1/runners/health"}
        response = health_check_module.lambda_handler(event, lambda_context)
        assert response["headers"]["Content-Type"] == "application/json"

    def test_03_returns_healthy_status(self, health_check_module, lambda_context):
        """Test health check returns healthy status."""
        event = {"httpMethod": "GET", "path": "/v1/runners/health"}
        response = health_check_module.lambda_handler(event, lambda_context)
        body = json.loads(response["body"])
        assert body["status"] == "healthy"

    def test_04_returns_timestamp(self, health_check_module, lambda_context):
        """Test health check returns timestamp."""
        event = {"httpMethod": "GET", "path": "/v1/runners/health"}
        response = health_check_module.lambda_handler(event, lambda_context)
        body = json.loads(response["body"])
        assert "timestamp" in body

    def test_05_returns_timestamp_as_integer(self, health_check_module, lambda_context):
        """Test health check timestamp is an integer."""
        event = {"httpMethod": "GET", "path": "/v1/runners/health"}
        response = health_check_module.lambda_handler(event, lambda_context)
        body = json.loads(response["body"])
        assert isinstance(body["timestamp"], int)

    def test_06_returns_service_name(self, health_check_module, lambda_context):
        """Test health check returns service name."""
        event = {"httpMethod": "GET", "path": "/v1/runners/health"}
        response = health_check_module.lambda_handler(event, lambda_context)
        body = json.loads(response["body"])
        assert body["service"] == "runners"

    def test_07_includes_cors_headers(self, health_check_module, lambda_context):
        """Test health check includes CORS headers."""
        event = {"httpMethod": "GET", "path": "/v1/runners/health"}
        response = health_check_module.lambda_handler(event, lambda_context)
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"


class TestHealthCheckOptionsMethod:
    """Tests for OPTIONS preflight requests."""

    def test_01_returns_200_for_options(self, health_check_module, lambda_context):
        """Test OPTIONS returns 200."""
        event = {"httpMethod": "OPTIONS", "path": "/v1/runners/health"}
        response = health_check_module.lambda_handler(event, lambda_context)
        assert response["statusCode"] == 200

    def test_02_includes_allow_methods(self, health_check_module, lambda_context):
        """Test OPTIONS includes allowed methods."""
        event = {"httpMethod": "OPTIONS", "path": "/v1/runners/health"}
        response = health_check_module.lambda_handler(event, lambda_context)
        assert "GET" in response["headers"]["Access-Control-Allow-Methods"]

    def test_03_includes_allow_origin(self, health_check_module, lambda_context):
        """Test OPTIONS includes allow origin."""
        event = {"httpMethod": "OPTIONS", "path": "/v1/runners/health"}
        response = health_check_module.lambda_handler(event, lambda_context)
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"

    def test_04_includes_allow_headers(self, health_check_module, lambda_context):
        """Test OPTIONS includes allowed headers."""
        event = {"httpMethod": "OPTIONS", "path": "/v1/runners/health"}
        response = health_check_module.lambda_handler(event, lambda_context)
        assert "Content-Type" in response["headers"]["Access-Control-Allow-Headers"]


class TestHealthCheckUnsupportedMethods:
    """Tests for unsupported HTTP methods."""

    def test_01_returns_405_for_post(self, health_check_module, lambda_context):
        """Test POST returns 405."""
        event = {"httpMethod": "POST", "path": "/v1/runners/health"}
        response = health_check_module.lambda_handler(event, lambda_context)
        assert response["statusCode"] == 405

    def test_02_returns_405_for_delete(self, health_check_module, lambda_context):
        """Test DELETE returns 405."""
        event = {"httpMethod": "DELETE", "path": "/v1/runners/health"}
        response = health_check_module.lambda_handler(event, lambda_context)
        assert response["statusCode"] == 405

    def test_03_returns_405_for_put(self, health_check_module, lambda_context):
        """Test PUT returns 405."""
        event = {"httpMethod": "PUT", "path": "/v1/runners/health"}
        response = health_check_module.lambda_handler(event, lambda_context)
        assert response["statusCode"] == 405

    def test_04_returns_error_message_for_unsupported(
        self, health_check_module, lambda_context
    ):
        """Test unsupported method returns error message."""
        event = {"httpMethod": "POST", "path": "/v1/runners/health"}
        response = health_check_module.lambda_handler(event, lambda_context)
        body = json.loads(response["body"])
        assert "error" in body

    def test_05_includes_cors_on_error(self, health_check_module, lambda_context):
        """Test CORS headers included on error response."""
        event = {"httpMethod": "POST", "path": "/v1/runners/health"}
        response = health_check_module.lambda_handler(event, lambda_context)
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
