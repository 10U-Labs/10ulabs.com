"""Post-deployment tests for SQS FIFO queue configuration.

These tests verify that the deployed SQS queues are correctly
configured as FIFO queues with content-based deduplication.
"""
import pytest
from test_fixtures.integration import create_sqs_fifo_queue_tests


# Create SQS FIFO queue tests for webhook queue - skip if not deployed yet
TestWebhookQueueFIFO = create_sqs_fifo_queue_tests(
    queue_name_fixture="webhook_queue_name",
    queue_description="Webhook queue",
    fail_on_missing=False,
)

# Create SQS FIFO queue tests for webhook DLQ - skip if not deployed yet
TestWebhookDLQFIFO = create_sqs_fifo_queue_tests(
    queue_name_fixture="webhook_dlq_name",
    queue_description="Webhook DLQ",
    fail_on_missing=False,
)
