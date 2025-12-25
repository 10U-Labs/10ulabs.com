"""Layer 5 tests: Verify API Gateway can send to FIFO queue.

These tests verify that the API Gateway integration can successfully
send messages to the FIFO SQS queue.
"""
import pytest
from test_fixtures.integration import create_sqs_fifo_queue_tests


# Create SQS FIFO queue tests - fail if queue doesn't exist (pre-deployment check)
TestSQSFIFOQueueAccess = create_sqs_fifo_queue_tests(
    queue_name_fixture="webhook_queue_name",
    queue_description="FIFO queue",
    fail_on_missing=True,
)
