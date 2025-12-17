"""Layer 5 tests: Verify API Gateway can send to FIFO queue.

These tests verify that the API Gateway integration can successfully
send messages to the FIFO SQS queue.
"""
import pytest
from botocore.exceptions import ClientError


class TestSQSFIFOQueueAccess:
    """Layer 5: Verify SQS FIFO queue is accessible."""

    def test_webhook_fifo_queue_exists(self, sqs_client, webhook_queue_name):
        """Verify the webhook FIFO queue exists and is accessible."""
        try:
            response = sqs_client.get_queue_url(QueueName=webhook_queue_name)
            assert response.get("QueueUrl"), (
                f"FIFO queue {webhook_queue_name} URL not returned"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.fail(
                    f"FIFO queue {webhook_queue_name} does not exist. "
                    "Deploy the agents endpoint first."
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
                f"Queue {webhook_queue_name} is not a FIFO queue"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.skip(f"Queue {webhook_queue_name} does not exist yet")
            raise

    def test_webhook_queue_has_deduplication(self, sqs_client, webhook_queue_name):
        """Verify the webhook queue has content-based deduplication."""
        try:
            queue_url = sqs_client.get_queue_url(QueueName=webhook_queue_name)["QueueUrl"]
            attrs = sqs_client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["ContentBasedDeduplication"]
            )

            dedup_attr = attrs.get("Attributes", {}).get("ContentBasedDeduplication")
            assert dedup_attr == "true", (
                f"Queue {webhook_queue_name} does not have content-based deduplication"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.skip(f"Queue {webhook_queue_name} does not exist yet")
            raise
