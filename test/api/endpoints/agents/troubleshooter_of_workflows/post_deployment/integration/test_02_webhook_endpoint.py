"""Integration tests for Troubleshooter of Workflows Webhook Endpoint.

These tests verify the Lambda function URL configuration without making
actual HTTP requests to the endpoint. E2E tests that make real HTTP calls
are in the e2e/ directory.
"""

import pytest


class TestWebhookEndpointExistence:
    """Verify the webhook endpoint exists and is configured correctly."""

    def test_01_webhook_url_is_configured(self, webhook_url):
        """Verify the Lambda has a function URL configured."""
        assert webhook_url is not None, (
            "Lambda function URL not configured. "
            "Run terraform apply in src/api/endpoints/agents/troubleshooter_of_workflows/"
        )

    def test_02_webhook_url_is_https(self, webhook_url):
        """Verify the webhook URL uses HTTPS."""
        if not webhook_url:
            pytest.skip("Webhook URL not configured")
        assert webhook_url.startswith("https://"), (
            f"Webhook URL should use HTTPS, got: {webhook_url}"
        )
