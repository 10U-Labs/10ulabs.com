"""Terraform unit tests for sqs.tf.

These tests verify the structure and configuration of SQS resources
defined in the Terraform configuration without making AWS calls.
"""

import re


class TestSQSQueueResources:
    """Test SQS queue resources exist."""

    def test_handler_queue_exists(self, sqs_tf_content):
        """Verify handler SQS queue is defined."""
        pattern = r'resource\s+"aws_sqs_queue"\s+"handler"'
        assert re.search(pattern, sqs_tf_content)

    def test_dlq_queue_exists(self, sqs_tf_content):
        """Verify DLQ SQS queue is defined."""
        pattern = r'resource\s+"aws_sqs_queue"\s+"handler_dlq"'
        assert re.search(pattern, sqs_tf_content)

    def test_queue_policy_exists(self, sqs_tf_content):
        """Verify SQS queue policy is defined."""
        pattern = r'resource\s+"aws_sqs_queue_policy"\s+"handler"'
        assert re.search(pattern, sqs_tf_content)

    def test_dlq_redrive_allow_policy_exists(self, sqs_tf_content):
        """Verify DLQ redrive allow policy is defined."""
        pattern = r'resource\s+"aws_sqs_queue_redrive_allow_policy"\s+"handler_dlq"'
        assert re.search(pattern, sqs_tf_content)


class TestHandlerQueueConfiguration:
    """Test handler queue configuration."""

    def test_queue_is_fifo(self, sqs_tf_content):
        """Verify handler queue is FIFO."""
        pattern = r'fifo_queue\s*=\s*true'
        assert re.search(pattern, sqs_tf_content)

    def test_queue_has_content_based_deduplication(self, sqs_tf_content):
        """Verify queue has content-based deduplication enabled."""
        pattern = r'content_based_deduplication\s*=\s*true'
        assert re.search(pattern, sqs_tf_content)

    def test_queue_has_visibility_timeout(self, sqs_tf_content):
        """Verify queue has visibility timeout of 300 seconds."""
        pattern = r'visibility_timeout_seconds\s*=\s*300'
        assert re.search(pattern, sqs_tf_content)

    def test_queue_has_message_retention(self, sqs_tf_content):
        """Verify queue has message retention of 86400 seconds (1 day)."""
        pattern = r'message_retention_seconds\s*=\s*86400'
        assert re.search(pattern, sqs_tf_content)

    def test_queue_has_redrive_policy(self, sqs_tf_content):
        """Verify queue has redrive policy to DLQ."""
        pattern = r'redrive_policy\s*=\s*jsonencode'
        assert re.search(pattern, sqs_tf_content)


class TestDLQConfiguration:
    """Test DLQ configuration."""

    def test_dlq_is_fifo(self, sqs_tf_content):
        """Verify DLQ is FIFO."""
        # Check the DLQ block specifically
        assert 'DLQ.fifo' in sqs_tf_content

    def test_dlq_has_14_day_retention(self, sqs_tf_content):
        """Verify DLQ has 14-day message retention (1209600 seconds)."""
        pattern = r'message_retention_seconds\s*=\s*1209600'
        assert re.search(pattern, sqs_tf_content)


class TestQueuePolicy:
    """Test SQS queue policy configuration."""

    def test_policy_allows_eventbridge(self, sqs_tf_content):
        """Verify queue policy allows EventBridge to send messages."""
        assert '"events.amazonaws.com"' in sqs_tf_content

    def test_policy_has_send_message_action(self, sqs_tf_content):
        """Verify queue policy allows sqs:SendMessage action."""
        assert '"sqs:SendMessage"' in sqs_tf_content


class TestRedriveConfiguration:
    """Test redrive configuration between main queue and DLQ."""

    def test_main_queue_redrives_to_dlq(self, sqs_tf_content):
        """Verify main queue has DLQ ARN in redrive policy."""
        pattern = r'deadLetterTargetArn\s*=\s*aws_sqs_queue\.handler_dlq\.arn'
        assert re.search(pattern, sqs_tf_content)

    def test_max_receive_count_is_three(self, sqs_tf_content):
        """Verify maxReceiveCount is 3."""
        pattern = r'maxReceiveCount\s*=\s*3'
        assert re.search(pattern, sqs_tf_content)

    def test_dlq_allows_redrive_from_main_queue(self, sqs_tf_content):
        """Verify DLQ allows redrive from main queue."""
        pattern = r'redrivePermission\s*=\s*"byQueue"'
        assert re.search(pattern, sqs_tf_content)
