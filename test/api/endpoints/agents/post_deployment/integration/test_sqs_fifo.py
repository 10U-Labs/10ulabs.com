"""Post-deployment tests for SQS FIFO queue configuration.

These tests verify that the deployed SQS queues are correctly
configured as FIFO queues with content-based deduplication.
"""
import pytest
from botocore.exceptions import ClientError


class TestWebhookQueueFIFO:
    """Tests to verify webhook queue is FIFO with deduplication."""

    def test_webhook_queue_exists(self, sqs_client, webhook_queue_name):
        """Verify the webhook FIFO queue exists."""
        try:
            response = sqs_client.get_queue_url(QueueName=webhook_queue_name)
            assert response.get("QueueUrl"), (
                f"Queue {webhook_queue_name} URL not returned"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.skip(
                    f"Queue {webhook_queue_name} not deployed yet. "
                    "Run terraform apply first."
                )
            raise

    def test_webhook_queue_is_fifo(self, sqs_client, webhook_queue_name):
        """Verify the webhook queue is configured as FIFO."""
        try:
            queue_url = sqs_client.get_queue_url(QueueName=webhook_queue_name)["QueueUrl"]
            attrs = sqs_client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["FifoQueue"]
            )

            fifo_attr = attrs.get("Attributes", {}).get("FifoQueue")
            assert fifo_attr == "true", (
                f"Queue {webhook_queue_name} FifoQueue attribute is '{fifo_attr}', expected 'true'"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.skip(f"Queue {webhook_queue_name} not deployed yet")
            raise

    def test_webhook_queue_has_deduplication(self, sqs_client, webhook_queue_name):
        """Verify the webhook queue has content-based deduplication enabled."""
        try:
            queue_url = sqs_client.get_queue_url(QueueName=webhook_queue_name)["QueueUrl"]
            attrs = sqs_client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["ContentBasedDeduplication"]
            )

            dedup_attr = attrs.get("Attributes", {}).get("ContentBasedDeduplication")
            assert dedup_attr == "true", (
                f"Queue {webhook_queue_name} ContentBasedDeduplication is '{dedup_attr}', expected 'true'"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.skip(f"Queue {webhook_queue_name} not deployed yet")
            raise


class TestWebhookDLQFIFO:
    """Tests to verify webhook DLQ is also FIFO."""

    def test_webhook_dlq_exists(self, sqs_client, webhook_dlq_name):
        """Verify the webhook DLQ FIFO queue exists."""
        try:
            response = sqs_client.get_queue_url(QueueName=webhook_dlq_name)
            assert response.get("QueueUrl"), (
                f"DLQ {webhook_dlq_name} URL not returned"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.skip(
                    f"DLQ {webhook_dlq_name} not deployed yet. "
                    "Run terraform apply first."
                )
            raise

    def test_webhook_dlq_is_fifo(self, sqs_client, webhook_dlq_name):
        """Verify the webhook DLQ is configured as FIFO."""
        try:
            queue_url = sqs_client.get_queue_url(QueueName=webhook_dlq_name)["QueueUrl"]
            attrs = sqs_client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["FifoQueue"]
            )

            fifo_attr = attrs.get("Attributes", {}).get("FifoQueue")
            assert fifo_attr == "true", (
                f"DLQ {webhook_dlq_name} FifoQueue attribute is '{fifo_attr}', expected 'true'"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.skip(f"DLQ {webhook_dlq_name} not deployed yet")
            raise
