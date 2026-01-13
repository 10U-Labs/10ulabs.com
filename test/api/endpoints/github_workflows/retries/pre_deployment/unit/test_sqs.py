"""Unit tests for sqs.tf configuration."""


class TestSqsConfiguration:
    """Tests for sqs.tf Terraform configuration."""

    def test_sqs_file_exists(self, retries_src_path):
        """Sqs.tf file exists."""
        assert (retries_src_path / "sqs.tf").exists()

    def test_main_queue_resource_exists(self, retries_src_path):
        """Main SQS queue resource is defined."""
        with open(retries_src_path / "sqs.tf", encoding="utf-8") as f:
            content = f.read()
        assert 'resource "aws_sqs_queue" "main"' in content

    def test_dlq_resource_exists(self, retries_src_path):
        """DLQ resource is defined."""
        with open(retries_src_path / "sqs.tf", encoding="utf-8") as f:
            content = f.read()
        assert 'resource "aws_sqs_queue" "dlq"' in content

    def test_main_queue_has_visibility_timeout(self, retries_src_path):
        """Main queue specifies visibility_timeout_seconds."""
        with open(retries_src_path / "sqs.tf", encoding="utf-8") as f:
            content = f.read()
        assert "visibility_timeout_seconds" in content

    def test_main_queue_has_message_retention(self, retries_src_path):
        """Main queue specifies message_retention_seconds."""
        with open(retries_src_path / "sqs.tf", encoding="utf-8") as f:
            content = f.read()
        assert "message_retention_seconds" in content

    def test_main_queue_has_redrive_policy(self, retries_src_path):
        """Main queue has redrive_policy for DLQ."""
        with open(retries_src_path / "sqs.tf", encoding="utf-8") as f:
            content = f.read()
        assert "redrive_policy" in content

    def test_dlq_referenced_in_redrive_policy(self, retries_src_path):
        """DLQ ARN is referenced in redrive policy."""
        with open(retries_src_path / "sqs.tf", encoding="utf-8") as f:
            content = f.read()
        assert "aws_sqs_queue.dlq.arn" in content

    def test_queue_policy_resource_exists(self, retries_src_path):
        """SQS queue policy resource is defined."""
        with open(retries_src_path / "sqs.tf", encoding="utf-8") as f:
            content = f.read()
        assert 'resource "aws_sqs_queue_policy"' in content

    def test_queue_policy_allows_lambda(self, retries_src_path):
        """Queue policy allows Lambda service."""
        with open(retries_src_path / "sqs.tf", encoding="utf-8") as f:
            content = f.read()
        assert "lambda.amazonaws.com" in content

    def test_queue_policy_allows_send_message(self, retries_src_path):
        """Queue policy allows SendMessage action."""
        with open(retries_src_path / "sqs.tf", encoding="utf-8") as f:
            content = f.read()
        assert "sqs:SendMessage" in content

    def test_queues_have_tags(self, retries_src_path):
        """Queues have tags."""
        with open(retries_src_path / "sqs.tf", encoding="utf-8") as f:
            content = f.read()
        assert "tags" in content

    def test_queues_use_common_tags(self, retries_src_path):
        """Queues use common_tags from locals."""
        with open(retries_src_path / "sqs.tf", encoding="utf-8") as f:
            content = f.read()
        assert "local.common_tags" in content
