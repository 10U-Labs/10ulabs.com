"""E2E tests for SQS integration.

User Journey: Verify SQS queue and DLQ are functioning correctly.

Critical Path: SQS queue → Lambda trigger → DLQ for failures
Failure Impact: Messages not processed, potential message loss.
"""
import json

import pytest
from botocore.exceptions import ClientError


class TestSQSQueueAccess:
    """Test SQS queue is accessible."""

    def test_queue_is_accessible(self, sqs_client, sqs_queue_url):
        """Verify SQS queue is accessible.

        User Journey: Queue access verification

        When: We check queue attributes
        Then: Queue responds with valid attributes
        """
        if not sqs_queue_url:
            pytest.skip("sqs_queue_url not available")

        try:
            response = sqs_client.get_queue_attributes(
                QueueUrl=sqs_queue_url,
                AttributeNames=["QueueArn", "ApproximateNumberOfMessages"]
            )
            assert "Attributes" in response
        except ClientError as e:
            pytest.fail(f"Cannot access SQS queue: {e}")

    def test_queue_has_arn(self, sqs_client, sqs_queue_url):
        """Verify SQS queue returns QueueArn attribute.

        User Journey: Queue attribute verification

        When: We request queue ARN
        Then: Queue returns valid ARN
        """
        if not sqs_queue_url:
            pytest.skip("sqs_queue_url not available")

        try:
            response = sqs_client.get_queue_attributes(
                QueueUrl=sqs_queue_url,
                AttributeNames=["QueueArn"]
            )
            assert "QueueArn" in response.get("Attributes", {})
        except ClientError as e:
            pytest.fail(f"Cannot access SQS queue: {e}")

    def test_queue_has_redrive_policy(self, sqs_client, sqs_queue_url):
        """Verify SQS queue has redrive policy configured.

        User Journey: DLQ configuration verification

        When: We check queue redrive policy
        Then: Queue has a redrive policy
        """
        if not sqs_queue_url:
            pytest.skip("sqs_queue_url not available")

        response = sqs_client.get_queue_attributes(
            QueueUrl=sqs_queue_url,
            AttributeNames=["RedrivePolicy"]
        )
        redrive_policy = response.get("Attributes", {}).get("RedrivePolicy", "")
        assert redrive_policy, "Queue has no redrive policy"

    def test_queue_redrive_has_dlq_target(self, sqs_client, sqs_queue_url):
        """Verify SQS queue redrive policy has DLQ target.

        User Journey: DLQ configuration verification

        When: We check queue redrive policy
        Then: Policy has deadLetterTargetArn configured
        """
        if not sqs_queue_url:
            pytest.skip("sqs_queue_url not available")

        response = sqs_client.get_queue_attributes(
            QueueUrl=sqs_queue_url,
            AttributeNames=["RedrivePolicy"]
        )
        redrive_policy = response.get("Attributes", {}).get("RedrivePolicy", "")
        if not redrive_policy:
            pytest.skip("No redrive policy configured")

        policy = json.loads(redrive_policy)
        assert "deadLetterTargetArn" in policy

    def test_queue_redrive_has_max_receive_count(self, sqs_client, sqs_queue_url):
        """Verify SQS queue redrive policy has maxReceiveCount.

        User Journey: DLQ configuration verification

        When: We check queue redrive policy
        Then: Policy has maxReceiveCount configured
        """
        if not sqs_queue_url:
            pytest.skip("sqs_queue_url not available")

        response = sqs_client.get_queue_attributes(
            QueueUrl=sqs_queue_url,
            AttributeNames=["RedrivePolicy"]
        )
        redrive_policy = response.get("Attributes", {}).get("RedrivePolicy", "")
        if not redrive_policy:
            pytest.skip("No redrive policy configured")

        policy = json.loads(redrive_policy)
        assert "maxReceiveCount" in policy


class TestSQSMessageSending:
    """Test sending messages to the SQS queue."""

    def test_can_send_message_to_queue(self, sqs_client, sqs_queue_url):
        """Verify messages can be sent to the queue.

        User Journey: Message publishing verification

        When: We send a test message to the queue
        Then: Message is accepted and we get a message ID
        """
        if not sqs_queue_url:
            pytest.skip("sqs_queue_url not available")

        # Send a test message with unmatched labels (so it won't actually route)
        test_message = {
            "job_id": 99998,
            "job_labels": ["test-only", "no-match"],
            "github_repo": "test/e2e-verification",
            "run_id": 99998
        }

        try:
            response = sqs_client.send_message(
                QueueUrl=sqs_queue_url,
                MessageBody=json.dumps(test_message),
                MessageAttributes={
                    "TestMessage": {
                        "DataType": "String",
                        "StringValue": "true"
                    }
                }
            )
            assert "MessageId" in response
        except ClientError as e:
            pytest.fail(f"Cannot send message to queue: {e}")


class TestDLQAccess:
    """Test DLQ is accessible."""

    def test_dlq_is_accessible(self, sqs_client, sqs_dlq_name):
        """Verify DLQ is accessible.

        User Journey: DLQ access verification

        When: We check DLQ attributes
        Then: DLQ responds with valid attributes
        """
        if not sqs_dlq_name:
            pytest.skip("sqs_dlq_name not available")

        try:
            # Get DLQ URL from name
            url_response = sqs_client.get_queue_url(QueueName=sqs_dlq_name)
            dlq_url = url_response["QueueUrl"]

            response = sqs_client.get_queue_attributes(
                QueueUrl=dlq_url,
                AttributeNames=["QueueArn", "ApproximateNumberOfMessages"]
            )
            assert "Attributes" in response
        except ClientError as e:
            if e.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.fail(f"DLQ '{sqs_dlq_name}' does not exist")
            pytest.fail(f"Cannot access DLQ: {e}")

    def test_dlq_has_arn(self, sqs_client, sqs_dlq_name):
        """Verify DLQ returns QueueArn attribute.

        User Journey: DLQ attribute verification

        When: We request DLQ ARN
        Then: DLQ returns valid ARN
        """
        if not sqs_dlq_name:
            pytest.skip("sqs_dlq_name not available")

        try:
            url_response = sqs_client.get_queue_url(QueueName=sqs_dlq_name)
            dlq_url = url_response["QueueUrl"]

            response = sqs_client.get_queue_attributes(
                QueueUrl=dlq_url,
                AttributeNames=["QueueArn"]
            )
            assert "QueueArn" in response.get("Attributes", {})
        except ClientError as e:
            if e.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                pytest.fail(f"DLQ '{sqs_dlq_name}' does not exist")
            pytest.fail(f"Cannot access DLQ: {e}")

    def test_dlq_retention_is_14_days(self, sqs_client, sqs_dlq_name):
        """Verify DLQ has 14-day message retention.

        User Journey: DLQ retention verification

        When: We check DLQ message retention
        Then: Messages are retained for 14 days (1209600 seconds)
        """
        if not sqs_dlq_name:
            pytest.skip("sqs_dlq_name not available")

        try:
            url_response = sqs_client.get_queue_url(QueueName=sqs_dlq_name)
            dlq_url = url_response["QueueUrl"]

            response = sqs_client.get_queue_attributes(
                QueueUrl=dlq_url,
                AttributeNames=["MessageRetentionPeriod"]
            )
            retention = int(response.get("Attributes", {}).get("MessageRetentionPeriod", 0))
            # 14 days = 1209600 seconds
            assert retention == 1209600, (
                f"DLQ retention is {retention}s, expected 1209600s (14 days)"
            )
        except ClientError as e:
            pytest.fail(f"Cannot get DLQ attributes: {e}")


class TestLambdaEventSourceMapping:
    """Test Lambda event source mapping configuration."""

    def test_lambda_has_sqs_trigger(self, lambda_client, lambda_function_name, sqs_queue_url):
        """Verify Lambda is triggered by the SQS queue.

        User Journey: Lambda trigger verification

        When: We check Lambda event source mappings
        Then: Queue is configured as an event source
        """
        if not lambda_function_name or not sqs_queue_url:
            pytest.skip("lambda_function_name or sqs_queue_url not available")

        try:
            response = lambda_client.list_event_source_mappings(
                FunctionName=lambda_function_name
            )
            mappings = response.get("EventSourceMappings", [])
            sqs_mappings = [
                m for m in mappings
                if "sqs" in m.get("EventSourceArn", "").lower()
            ]
            assert len(sqs_mappings) > 0, (
                f"Lambda {lambda_function_name} has no SQS event source mappings"
            )
        except ClientError as e:
            pytest.fail(f"Cannot list event source mappings: {e}")

    def test_event_source_is_enabled(self, lambda_client, lambda_function_name):
        """Verify Lambda event source mapping is enabled.

        User Journey: Event source state verification

        When: We check Lambda event source mappings
        Then: At least one SQS mapping is enabled
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        try:
            response = lambda_client.list_event_source_mappings(
                FunctionName=lambda_function_name
            )
            mappings = response.get("EventSourceMappings", [])
            sqs_mappings = [
                m for m in mappings
                if "sqs" in m.get("EventSourceArn", "").lower()
            ]
            if not sqs_mappings:
                pytest.skip("No SQS event source mappings found")

            enabled_mappings = [m for m in sqs_mappings if m.get("State") == "Enabled"]
            assert len(enabled_mappings) > 0, (
                "No SQS event source mappings are enabled"
            )
        except ClientError as e:
            pytest.fail(f"Cannot list event source mappings: {e}")
