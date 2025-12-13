"""Tests to validate SQS workflow configuration is correctly defined.

These tests verify that the SQS queue Terraform configuration is valid and follows
the expected naming conventions. This is pre-deployment validation of infrastructure
configuration, not post-deployment verification that resources exist.

Five-layer testing model:
- Layer 3: Existence - Are the queue definitions extractable from Terraform?
- Layer 4: Configuration - Do queue names follow expected naming conventions?
"""
from pathlib import Path

from terraform_config import extract_sqs_queue_names, get_runners_resource_names


RUNNERS_SRC = Path(__file__).parents[6] / "src" / "api" / "endpoints" / "runners"
SQS_TF_FILE = RUNNERS_SRC / "sqs.tf"


class TestSqsQueueTerraformConfig:
    """Layer 3: Verify SQS queue definitions are extractable from Terraform."""

    def test_sqs_tf_file_exists(self):
        """Verify sqs.tf file exists in runners endpoint."""
        assert SQS_TF_FILE.exists(), (
            f"sqs.tf not found at {SQS_TF_FILE}. "
            "The runners endpoint requires SQS queue definitions."
        )

    def test_sqs_queues_extractable(self):
        """Verify SQS queue names can be extracted from sqs.tf."""
        queues = extract_sqs_queue_names(SQS_TF_FILE)
        assert len(queues) > 0, (
            "No SQS queue definitions found in sqs.tf. "
            "Expected at least one aws_sqs_queue resource."
        )

    def test_webhook_ingress_queue_defined(self):
        """Verify webhook_ingress queue is defined in Terraform."""
        queues = extract_sqs_queue_names(SQS_TF_FILE)
        queue_resources = [name for name, _ in queues]
        assert "webhook_ingress" in queue_resources, (
            "webhook_ingress queue not found in sqs.tf. "
            "Required for API Gateway → SQS direct integration."
        )

    def test_webhook_ingress_dlq_defined(self):
        """Verify webhook_ingress_dlq is defined in Terraform."""
        queues = extract_sqs_queue_names(SQS_TF_FILE)
        queue_resources = [name for name, _ in queues]
        assert "webhook_ingress_dlq" in queue_resources, (
            "webhook_ingress_dlq not found in sqs.tf. "
            "Required for failed webhook ingress message handling."
        )

    def test_ignored_events_queue_defined(self):
        """Verify ignored_events queue is defined in Terraform."""
        queues = extract_sqs_queue_names(SQS_TF_FILE)
        queue_resources = [name for name, _ in queues]
        assert "ignored_events" in queue_resources, (
            "ignored_events queue not found in sqs.tf. "
            "Required for storing unhandled webhook events."
        )

    def test_cleanup_queue_defined(self):
        """Verify cleanup_queue is defined in Terraform."""
        queues = extract_sqs_queue_names(SQS_TF_FILE)
        queue_resources = [name for name, _ in queues]
        assert "cleanup_queue" in queue_resources, (
            "cleanup_queue not found in sqs.tf. "
            "Required for workflow_run completed event handling."
        )

    def test_job_queue_defined(self):
        """Verify job_queue is defined in Terraform."""
        queues = extract_sqs_queue_names(SQS_TF_FILE)
        queue_resources = [name for name, _ in queues]
        assert "job_queue" in queue_resources, (
            "job_queue not found in sqs.tf. "
            "Required for workflow_job queued event handling."
        )


class TestSqsQueueNamingConventions:
    """Layer 4: Verify SQS queue names follow expected conventions."""

    def test_queue_names_use_handler_prefix(self):
        """Verify queue names use the webhook handler name as prefix."""
        resource_names = get_runners_resource_names()
        # All queues should have a consistent prefix pattern
        expected_queues = [
            resource_names['job_queue'],
            resource_names['job_dlq'],
            resource_names['webhook_dlq'],
            resource_names['webhook_ingress_queue'],
            resource_names['webhook_ingress_dlq'],
            resource_names['ignored_events_queue'],
            resource_names['ignored_events_dlq'],
            resource_names['cleanup_queue'],
            resource_names['cleanup_dlq'],
        ]
        # All should start with TenULabs (or the configured prefix)
        for queue_name in expected_queues:
            assert queue_name.startswith('TenULabs'), (
                f"Queue {queue_name} doesn't follow naming convention. "
                "Expected to start with resource prefix."
            )

    def test_dlq_names_include_dlq_suffix(self):
        """Verify DLQ names include 'Dlq' suffix."""
        resource_names = get_runners_resource_names()
        dlq_keys = [k for k in resource_names if 'dlq' in k]
        for key in dlq_keys:
            queue_name = resource_names[key]
            assert 'Dlq' in queue_name, (
                f"DLQ {key}={queue_name} doesn't include 'Dlq' suffix. "
                "DLQ names should clearly indicate dead letter queue purpose."
            )

    def test_ingress_queue_short_retention_configured(self):
        """Verify ingress queue is configured with short retention for DDoS protection."""
        with open(SQS_TF_FILE, encoding='utf-8') as f:
            content = f.read()
        # Check for message_retention_seconds = 3600 in webhook_ingress resource
        assert 'message_retention_seconds  = 3600' in content or \
               'message_retention_seconds = 3600' in content, (
            "webhook_ingress queue should have 1-hour retention (3600 seconds) "
            "for DDoS protection."
        )
