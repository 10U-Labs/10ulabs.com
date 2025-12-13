"""Tests to validate SQS queues before runners deployment.

These tests run after test_01_iam_credentials.py to ensure we have valid
credentials before testing SQS resources.

Five-layer testing model:
- Layer 2: Authorization - Can we call SQS APIs?
- Layer 3: Existence - Do the required queues exist?
- Layer 4: Configuration - Are queues configured correctly?
- Layer 5: Capability - Can we perform required operations?
"""

import json
import uuid

from botocore.exceptions import ClientError
import pytest


# =============================================================================
# Layer 2: Authorization
# =============================================================================

def test_01_can_call_get_queue_url_api(sqs_client, config):
    """Layer 2: Verify we have permission to call sqs:GetQueueUrl."""
    queue_name = config['job_queue_name']
    try:
        sqs_client.get_queue_url(QueueName=queue_name)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "AccessDenied":
            pytest.fail(
                f"No permission to call GetQueueUrl for '{queue_name}'. "
                "Check IAM permissions for sqs:GetQueueUrl."
            )
        if code == "AWS.SimpleQueueService.NonExistentQueue":
            pass  # Queue doesn't exist, but we have permission
        else:
            raise


# =============================================================================
# Layer 3: Existence - All Queues
# =============================================================================

class TestSQSQueuesExistence:
    """Layer 3: Verify all required SQS queues exist."""

    def test_01_job_queue_exists(self, sqs_client, config):
        """Verify the job queue exists."""
        queue_name = config['job_queue_name']
        try:
            response = sqs_client.get_queue_url(QueueName=queue_name)
            assert response.get("QueueUrl") is not None
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.fail(
                    f"SQS queue '{queue_name}' does not exist. "
                    "Run terraform apply in src/api/endpoints/runners/"
                )
            raise

    def test_02_job_dlq_exists(self, sqs_client, config):
        """Verify the job DLQ exists."""
        queue_name = config['job_dlq_name']
        try:
            response = sqs_client.get_queue_url(QueueName=queue_name)
            assert response.get("QueueUrl") is not None
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.fail(
                    f"SQS queue '{queue_name}' does not exist. "
                    "Run terraform apply in src/api/endpoints/runners/"
                )
            raise

    def test_03_webhook_dlq_exists(self, sqs_client, config):
        """Verify the webhook DLQ exists."""
        queue_name = config['webhook_dlq_name']
        try:
            response = sqs_client.get_queue_url(QueueName=queue_name)
            assert response.get("QueueUrl") is not None
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.fail(
                    f"SQS queue '{queue_name}' does not exist. "
                    "Run terraform apply in src/api/endpoints/runners/"
                )
            raise

    def test_04_drift_recovery_queue_exists(self, sqs_client, config):
        """Verify the drift recovery FIFO queue exists."""
        queue_name = config['drift_recovery_queue_name']
        try:
            response = sqs_client.get_queue_url(QueueName=queue_name)
            assert response.get("QueueUrl") is not None
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.fail(
                    f"SQS FIFO queue '{queue_name}' does not exist. "
                    "Run terraform apply in src/api/endpoints/runners/"
                )
            raise


# =============================================================================
# Layer 4: Configuration - Job Queue
# =============================================================================

class TestJobQueueConfiguration:
    """Layer 4: Verify the job queue is configured correctly."""

    def test_01_job_queue_has_dlq_configured(self, sqs_client, config):
        """Verify the job queue has a dead-letter queue configured."""
        queue_name = config['job_queue_name']
        try:
            url_response = sqs_client.get_queue_url(QueueName=queue_name)
            queue_url = url_response["QueueUrl"]
            attrs_response = sqs_client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["RedrivePolicy"]
            )
            redrive_policy = attrs_response.get("Attributes", {}).get("RedrivePolicy")
            assert redrive_policy is not None, (
                f"Queue '{queue_name}' has no dead-letter queue configured. "
                "RedrivePolicy should be set for error handling."
            )
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.skip(f"Queue '{queue_name}' does not exist")
            raise

    def test_02_job_queue_has_visibility_timeout(self, sqs_client, config):
        """Verify the job queue has appropriate visibility timeout."""
        queue_name = config['job_queue_name']
        try:
            url_response = sqs_client.get_queue_url(QueueName=queue_name)
            queue_url = url_response["QueueUrl"]
            attrs_response = sqs_client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["VisibilityTimeout"]
            )
            timeout = int(attrs_response["Attributes"]["VisibilityTimeout"])
            assert timeout >= 30, (
                f"Queue '{queue_name}' visibility timeout ({timeout}s) too low. "
                "Should be at least 30 seconds for Lambda processing."
            )
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.skip(f"Queue '{queue_name}' does not exist")
            raise


# =============================================================================
# Layer 4: Configuration - Drift Recovery Queue
# =============================================================================

class TestDriftRecoveryQueueConfiguration:
    """Layer 4: Verify the drift recovery queue is configured correctly."""

    def test_01_drift_recovery_queue_is_fifo(self, sqs_client, config):
        """Verify the drift recovery queue is a FIFO queue."""
        queue_name = config['drift_recovery_queue_name']
        try:
            url_response = sqs_client.get_queue_url(QueueName=queue_name)
            queue_url = url_response["QueueUrl"]
            attrs_response = sqs_client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["FifoQueue"]
            )
            is_fifo = attrs_response["Attributes"].get("FifoQueue") == "true"
            assert is_fifo, (
                f"Queue '{queue_name}' is not a FIFO queue. "
                "Drift recovery requires ordered message processing."
            )
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.skip(f"Queue '{queue_name}' does not exist")
            raise

    def test_02_drift_recovery_queue_has_deduplication(self, sqs_client, config):
        """Verify the drift recovery queue has content-based deduplication."""
        queue_name = config['drift_recovery_queue_name']
        try:
            url_response = sqs_client.get_queue_url(QueueName=queue_name)
            queue_url = url_response["QueueUrl"]
            attrs_response = sqs_client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["ContentBasedDeduplication"]
            )
            has_dedup = attrs_response["Attributes"].get(
                "ContentBasedDeduplication"
            ) == "true"
            assert has_dedup, (
                f"Queue '{queue_name}' missing content-based deduplication. "
                "FIFO queues should use deduplication to prevent duplicate processing."
            )
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.skip(f"Queue '{queue_name}' does not exist")
            raise


# =============================================================================
# Layer 5: Capability - Job Queue
# =============================================================================

class TestJobQueueCapability:
    """Layer 5: Verify we can perform operations on the job queue."""

    def test_01_can_send_message(self, sqs_client, config):
        """Verify we can send messages to the job queue."""
        queue_name = config['job_queue_name']
        test_id = f"pre-deployment-test-{uuid.uuid4()}"
        try:
            url_response = sqs_client.get_queue_url(QueueName=queue_name)
            queue_url = url_response["QueueUrl"]
            sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps({"test_id": test_id}),
                MessageAttributes={
                    "TestType": {
                        "DataType": "String",
                        "StringValue": "pre-deployment-test"
                    }
                }
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to send messages to '{queue_name}'. "
                    "Check IAM permissions for sqs:SendMessage."
                )
            raise

    def test_02_can_receive_message(self, sqs_client, config):
        """Verify we can receive messages from the job queue."""
        queue_name = config['job_queue_name']
        try:
            url_response = sqs_client.get_queue_url(QueueName=queue_name)
            queue_url = url_response["QueueUrl"]
            sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=0
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to receive messages from '{queue_name}'. "
                    "Check IAM permissions for sqs:ReceiveMessage."
                )
            raise
