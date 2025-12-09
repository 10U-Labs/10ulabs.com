"""E2E tests for Troubleshooter of Workflows Webhook Endpoint.

These tests make real HTTP requests to the deployed Lambda function URL
to verify the full request/response cycle works correctly.
"""

import pytest
import requests


class TestWebhookEndpointReachability:
    """Verify the webhook endpoint is reachable and responds."""

    def test_01_webhook_url_is_reachable(self, webhook_url):
        """Verify the webhook endpoint is reachable."""
        if not webhook_url:
            pytest.skip("Webhook URL not configured")
        try:
            # Empty POST should return 200 (ignored event)
            response = requests.post(
                webhook_url,
                json={},
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            # Should not get connection errors
            assert response.status_code in [200, 400, 500], (
                f"Unexpected status code: {response.status_code}"
            )
        except requests.exceptions.ConnectionError as err:
            pytest.fail(f"Cannot connect to webhook URL: {err}")
        except requests.exceptions.Timeout:
            pytest.fail("Webhook URL timed out after 30 seconds")


class TestWebhookEventHandling:
    """Verify the webhook handles events correctly via real HTTP calls."""

    def test_01_ignores_non_completed_action(self, webhook_url):
        """Verify webhook ignores non-completed workflow_run events."""
        if not webhook_url:
            pytest.skip("Webhook URL not configured")

        payload = {
            "action": "requested",
            "workflow_run": {
                "id": 12345,
                "name": "Test Workflow",
                "conclusion": None,
            },
            "repository": {
                "name": "test-repo",
                "owner": {"login": "test-org"},
            },
        }

        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        assert response.status_code == 200
        body = response.json()
        assert "message" in body
        assert "non-completed" in body["message"].lower(), (
            f"Expected 'non-completed' in response, got: {body}"
        )

    def test_02_ignores_successful_workflow(self, webhook_url):
        """Verify webhook ignores successful workflow_run events."""
        if not webhook_url:
            pytest.skip("Webhook URL not configured")

        payload = {
            "action": "completed",
            "workflow_run": {
                "id": 12345,
                "name": "Test Workflow",
                "conclusion": "success",
            },
            "repository": {
                "name": "test-repo",
                "owner": {"login": "test-org"},
            },
        }

        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        assert response.status_code == 200
        body = response.json()
        assert "message" in body
        assert "success" in body["message"].lower(), (
            f"Expected 'success' in response, got: {body}"
        )

    def test_03_ignores_troubleshooter_of_workflows_workflow(self, webhook_url):
        """Verify webhook ignores its own troubleshooter-of-workflows workflows."""
        if not webhook_url:
            pytest.skip("Webhook URL not configured")

        payload = {
            "action": "completed",
            "workflow_run": {
                "id": 12345,
                "name": "Deploying Troubleshooter-of-Workflows Agent",
                "conclusion": "failure",
            },
            "repository": {
                "name": "test-repo",
                "owner": {"login": "test-org"},
            },
        }

        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        assert response.status_code == 200
        body = response.json()
        assert "message" in body
        assert "troubleshooter-of-workflows" in body["message"].lower(), (
            f"Expected 'troubleshooter-of-workflows' in response, got: {body}"
        )


class TestScheduledScanMode:
    """Verify scheduled scan mode works via real HTTP calls."""

    def test_01_scheduled_event_triggers_scan(self, webhook_url):
        """Verify scheduled event triggers scan mode detection.

        Uses test_mode=True to skip the actual scan (which can take minutes
        depending on how many unresolved failures exist). This validates
        the mode detection logic without triggering real GitHub API calls.
        """
        if not webhook_url:
            pytest.skip("Webhook URL not configured")

        # Simulate EventBridge scheduled event with test_mode
        payload = {
            "source": "aws.events",
            "detail-type": "Scheduled Event",
            "test_mode": True,
        }

        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        assert response.status_code == 200
        body = response.json()
        assert body.get("mode") == "scheduled", (
            f"Expected mode 'scheduled', got: {body}"
        )
        assert "processed" in body, (
            f"Expected 'processed' count in response, got: {body}"
        )
        assert body.get("test_mode") is True, (
            f"Expected test_mode=True in response, got: {body}"
        )
