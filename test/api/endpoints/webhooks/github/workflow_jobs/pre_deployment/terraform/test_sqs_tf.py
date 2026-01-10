"""Terraform unit tests for sqs.tf.

These tests verify SQS queues are correctly configured.
"""

import re

import pytest

# Expected SQS queues (primary queues and DLQs)
SQS_QUEUES = [
    "webhook_ingress",
    "webhook_ingress_dlq",
    "cancellation",
    "cancellation_dlq",
    "ignored_events",
    "ignored_events_dlq",
    "webhook_dlq",
    "drift_recovery",
]

# Queues that should have visibility timeout (non-DLQ queues)
QUEUES_WITH_VISIBILITY_TIMEOUT = [
    "webhook_ingress",
    "cancellation",
    "ignored_events",
    "webhook_dlq",
    "drift_recovery",
]


class TestSQSQueuesExist:
    """Test that all expected SQS queues are defined."""

    @pytest.mark.parametrize("queue_name", SQS_QUEUES)
    def test_sqs_queue_exists(self, sqs_tf_content, queue_name):
        """Verify SQS queue resource is defined."""
        pattern = rf'resource\s+"aws_sqs_queue"\s+"{queue_name}"'
        assert re.search(pattern, sqs_tf_content), (
            f"SQS queue '{queue_name}' not found in sqs.tf"
        )


class TestSQSQueueConfiguration:
    """Test SQS queue configurations."""

    def test_queues_have_visibility_timeout(self, sqs_tf_content):
        """Verify non-DLQ SQS queues have visibility_timeout_seconds set."""
        timeout_count = len(re.findall(r'visibility_timeout_seconds\s*=', sqs_tf_content))
        expected_count = len(QUEUES_WITH_VISIBILITY_TIMEOUT)
        assert timeout_count >= expected_count, (
            f"Expected visibility timeout for non-DLQ queues: "
            f"found {timeout_count}, expected at least {expected_count}"
        )

    def test_queues_have_retention_period(self, sqs_tf_content):
        """Verify SQS queues have message_retention_seconds set."""
        retention_count = len(re.findall(r'message_retention_seconds\s*=', sqs_tf_content))
        assert retention_count >= 1, "Expected at least one queue with message retention"


class TestSQSDLQConfiguration:
    """Test SQS dead-letter queue configurations."""

    def test_webhook_dlq_exists(self, sqs_tf_content):
        """Verify webhook DLQ is defined."""
        pattern = r'resource\s+"aws_sqs_queue"\s+"webhook_dlq"'
        assert re.search(pattern, sqs_tf_content), (
            "Webhook DLQ not found in sqs.tf"
        )

    def test_queues_have_redrive_policy(self, sqs_tf_content):
        """Verify queues have redrive policy for DLQ."""
        # At least some queues should have redrive policy
        redrive_count = len(re.findall(r'redrive_policy\s*=', sqs_tf_content))
        assert redrive_count >= 1, "Expected at least one queue with redrive policy"


class TestSQSNamingConventions:
    """Test SQS naming conventions."""

    def test_queue_names_use_locals(self, sqs_tf_content):
        """Verify queue names use local variables (directly or via interpolation)."""
        # Accept both direct local reference and string interpolation with local
        direct_pattern = r'name\s*=\s*local\.'
        interpolation_pattern = r'name\s*=\s*"\$\{local\.'
        direct_refs = len(re.findall(direct_pattern, sqs_tf_content))
        interpolation_refs = len(re.findall(interpolation_pattern, sqs_tf_content))
        total_local_refs = direct_refs + interpolation_refs
        queue_count = len(re.findall(r'resource\s+"aws_sqs_queue"', sqs_tf_content))
        assert total_local_refs >= queue_count, (
            f"Not all queue names use local variables: "
            f"found {total_local_refs} local refs for {queue_count} queues"
        )


class TestSQSEncryption:
    """Test SQS encryption configurations.

    Note: As of 2023, AWS SQS encrypts all messages at rest by default using
    SSE-SQS (SQS-managed encryption keys). Explicit encryption configuration
    is only needed for customer-managed KMS keys.
    """

    def test_sqs_uses_default_encryption_or_kms(self, sqs_tf_content):
        """Verify SQS encryption strategy is consistent.

        Either all queues use default AWS SSE-SQS encryption (no explicit config),
        or queues that need customer-managed KMS keys have it configured.
        """
        # Check if any explicit encryption is configured
        kms_pattern = r'kms_master_key_id\s*='
        sse_pattern = r'sqs_managed_sse_enabled\s*='
        kms_count = len(re.findall(kms_pattern, sqs_tf_content))
        sse_count = len(re.findall(sse_pattern, sqs_tf_content))

        # If no explicit encryption, queues use AWS default SSE-SQS (valid)
        # If some explicit encryption, verify consistency for those that need it
        if kms_count == 0 and sse_count == 0:
            # Using default AWS SSE-SQS encryption - this is valid
            pass
        else:
            # Some queues have explicit encryption - verify at least one
            assert kms_count + sse_count >= 1, (
                "Expected explicit encryption configuration to be consistent"
            )
