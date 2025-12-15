"""End-to-end tests for agents webhook endpoint."""
import json

import pytest
import requests


class TestWebhookEndpoint:
    """E2E tests for the webhook endpoint."""

    @pytest.fixture
    def webhook_url(self, shared_config):
        """Get the webhook Function URL."""
        # The Function URL is output from Terraform
        # For now, we construct it from the shared config
        aws_region = shared_config.get("aws_region", "us-east-2")
        resource_prefix = shared_config.get("resource_prefix", "10ulabs")

        # Function URL format: https://{url-id}.lambda-url.{region}.on.aws/
        # We need to get this from Terraform outputs or environment
        # For now, skip if not available
        import os
        webhook_url = os.environ.get("AGENTS_WEBHOOK_URL")
        if not webhook_url:
            pytest.skip(
                "AGENTS_WEBHOOK_URL environment variable not set. "
                "Set it to the Lambda Function URL to run e2e tests."
            )
        return webhook_url

    def test_webhook_responds_to_health_check(self, webhook_url):
        """Test that webhook endpoint responds to requests."""
        # Send a minimal event that should be skipped
        event = {
            "action": "queued",  # Not 'completed', so should be skipped
            "workflow_run": {"conclusion": "pending"},
        }

        response = requests.post(
            webhook_url,
            json=event,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        assert response.status_code == 200, (
            f"Webhook should respond with 200, got {response.status_code}: "
            f"{response.text}"
        )

    def test_webhook_skips_non_failure_events_returns_200(self, webhook_url):
        """Test that webhook returns 200 for non-failure workflow events."""
        event = {
            "action": "completed",
            "workflow_run": {
                "id": 12345,
                "name": "Test Workflow",
                "conclusion": "success",  # Not a failure
            },
            "repository": {
                "name": "test-repo",
                "owner": {"login": "test-owner"},
            },
        }

        response = requests.post(
            webhook_url,
            json=event,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        assert response.status_code == 200

    def test_webhook_skips_non_failure_events_indicates_skip(self, webhook_url):
        """Test that webhook response indicates event was skipped."""
        event = {
            "action": "completed",
            "workflow_run": {
                "id": 12345,
                "name": "Test Workflow",
                "conclusion": "success",  # Not a failure
            },
            "repository": {
                "name": "test-repo",
                "owner": {"login": "test-owner"},
            },
        }

        response = requests.post(
            webhook_url,
            json=event,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        body = response.json()
        assert "success" in str(body).lower() or "ignoring" in str(body).lower()

    def test_webhook_returns_200_for_queued_event(self, webhook_url):
        """Test that webhook returns 200 for queued event."""
        event = {"action": "queued"}

        response = requests.post(
            webhook_url,
            json=event,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        assert response.status_code == 200

    def test_webhook_returns_json_dict_response(self, webhook_url):
        """Test that webhook returns JSON dict response."""
        event = {"action": "queued"}

        response = requests.post(
            webhook_url,
            json=event,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        try:
            body = response.json()
            assert isinstance(body, dict)
        except json.JSONDecodeError:
            pytest.fail("Response should be valid JSON")


class TestScheduledScan:
    """E2E tests for scheduled scan functionality."""

    @pytest.fixture
    def webhook_url(self, shared_config):
        """Get the webhook Function URL."""
        import os
        webhook_url = os.environ.get("AGENTS_WEBHOOK_URL")
        if not webhook_url:
            pytest.skip("AGENTS_WEBHOOK_URL environment variable not set")
        return webhook_url

    def test_scheduled_scan_in_test_mode_returns_200(self, webhook_url):
        """Test scheduled scan with test_mode returns 200."""
        event = {
            "source": "aws.events",
            "detail-type": "Scheduled Event",
            "test_mode": True,
        }

        response = requests.post(
            webhook_url,
            json=event,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        assert response.status_code == 200

    def test_scheduled_scan_in_test_mode_indicates_test_mode(self, webhook_url):
        """Test scheduled scan response indicates test mode."""
        event = {
            "source": "aws.events",
            "detail-type": "Scheduled Event",
            "test_mode": True,
        }

        response = requests.post(
            webhook_url,
            json=event,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        body = response.json()
        assert body.get("test_mode") is True or "test" in str(body).lower()
