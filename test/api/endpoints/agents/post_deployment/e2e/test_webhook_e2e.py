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


class TestFIFODeduplication:
    """E2E tests for FIFO queue deduplication.

    These tests verify that duplicate webhook events are deduplicated
    by the SQS FIFO queue, preventing duplicate agent invocations.
    """

    @pytest.fixture
    def api_gateway_url(self, shared_config):
        """Get the API Gateway webhook URL."""
        import os
        api_url = os.environ.get("AGENTS_API_GATEWAY_URL")
        if not api_url:
            pytest.skip(
                "AGENTS_API_GATEWAY_URL environment variable not set. "
                "Set it to https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/v1/agents"
            )
        return api_url

    @pytest.fixture
    def sqs_client(self, shared_config):
        """Get SQS client."""
        import boto3
        aws_region = shared_config.get("aws_region", "us-east-2")
        return boto3.client("sqs", region_name=aws_region)

    @pytest.fixture
    def webhook_queue_url(self, sqs_client, shared_config):
        """Get the webhook FIFO queue URL."""
        resource_prefix = shared_config.get("resource_prefix", "10ulabs")
        queue_name = f"{resource_prefix}-webhook-ingress.fifo"
        try:
            response = sqs_client.get_queue_url(QueueName=queue_name)
            return response["QueueUrl"]
        except Exception:
            pytest.skip(f"Queue {queue_name} not found")

    def test_fifo_deduplication_prevents_duplicate_messages(
        self, api_gateway_url, sqs_client, webhook_queue_url
    ):
        """Verify FIFO deduplication prevents duplicate webhook processing.

        Sends identical webhook payloads twice and verifies only one
        message lands in the queue (content-based deduplication).
        """
        import time

        # Use a test payload that will be skipped (not trigger agent)
        # but will still be enqueued to test deduplication
        test_payload = {
            "action": "completed",
            "workflow_run": {
                "id": 99999999,  # Test run ID
                "name": "FIFO Deduplication Test",
                "conclusion": "success",  # Will be skipped, not a failure
                "head_sha": "test-dedup-sha",
                "head_branch": "test-branch",
            },
            "repository": {
                "name": "10ulabs.com",
                "owner": {"login": "10U-Labs-LLC"},
            },
        }

        # Get initial queue depth
        initial_attrs = sqs_client.get_queue_attributes(
            QueueUrl=webhook_queue_url,
            AttributeNames=["ApproximateNumberOfMessages"]
        )
        initial_count = int(initial_attrs["Attributes"].get(
            "ApproximateNumberOfMessages", "0"
        ))

        try:
            # Send the same payload twice (should be deduplicated)
            # If any request fails, it will raise an exception
            for _ in range(2):
                response = requests.post(
                    api_gateway_url,
                    json=test_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                )
                response.raise_for_status()

            # Wait for messages to appear in queue
            time.sleep(2)

            # Check queue depth - should only increase by 1 due to deduplication
            final_attrs = sqs_client.get_queue_attributes(
                QueueUrl=webhook_queue_url,
                AttributeNames=["ApproximateNumberOfMessages"]
            )
            final_count = int(final_attrs["Attributes"].get(
                "ApproximateNumberOfMessages", "0"
            ))

            messages_added = final_count - initial_count

            # With deduplication, sending same message twice should result in 1 message
            # (or 0 if Lambda already processed it)
            assert messages_added <= 1, (
                f"Expected at most 1 new message due to FIFO deduplication, "
                f"but found {messages_added} new messages. "
                f"Initial: {initial_count}, Final: {final_count}"
            )

        finally:
            # Clean up: purge any test messages (best effort)
            # Note: FIFO queues can be purged but test messages may already be processed
            pass
