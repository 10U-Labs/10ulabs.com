"""Unit tests for agents SQS Terraform configuration."""
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


def test_sqs_terraform_file_exists():
    """Verify sqs.tf file exists."""
    sqs_file = AGENTS_SRC / "sqs.tf"
    assert sqs_file.exists()


def test_webhook_ingress_queue_exists():
    """Verify webhook ingress SQS queue is defined."""
    sqs_file = AGENTS_SRC / "sqs.tf"
    with open(sqs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_sqs_queue" "webhook_ingress"' in content


def test_webhook_dlq_exists():
    """Verify webhook DLQ is defined."""
    sqs_file = AGENTS_SRC / "sqs.tf"
    with open(sqs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_sqs_queue" "webhook_dlq"' in content


def test_scanner_queue_exists():
    """Verify scanner SQS queue is defined."""
    sqs_file = AGENTS_SRC / "sqs.tf"
    with open(sqs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_sqs_queue" "scanner"' in content


def test_scanner_dlq_exists():
    """Verify scanner DLQ is defined."""
    sqs_file = AGENTS_SRC / "sqs.tf"
    with open(sqs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_sqs_queue" "scanner_dlq"' in content


def test_invoker_ingress_queue_exists():
    """Verify invoker ingress SQS queue is defined."""
    sqs_file = AGENTS_SRC / "sqs.tf"
    with open(sqs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_sqs_queue" "invoker_ingress"' in content


def test_invoker_dlq_exists():
    """Verify invoker DLQ is defined."""
    sqs_file = AGENTS_SRC / "sqs.tf"
    with open(sqs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_sqs_queue" "invoker_dlq"' in content


def test_eventbridge_rule_exists():
    """Verify EventBridge scheduled rule is defined."""
    sqs_file = AGENTS_SRC / "sqs.tf"
    with open(sqs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_event_rule" "scheduled_scan"' in content


def test_eventbridge_targets_sqs():
    """Verify EventBridge targets the scanner SQS queue."""
    sqs_file = AGENTS_SRC / "sqs.tf"
    with open(sqs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_event_target" "scheduled_scan_sqs"' in content


def test_scanner_queue_policy_exists():
    """Verify scanner SQS queue policy for EventBridge is defined."""
    sqs_file = AGENTS_SRC / "sqs.tf"
    with open(sqs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_sqs_queue_policy" "scanner_eventbridge"' in content


def test_webhook_queue_has_fifo_attribute():
    """Verify webhook ingress queue has fifo_queue attribute."""
    sqs_file = AGENTS_SRC / "sqs.tf"
    with open(sqs_file, encoding="utf-8") as f:
        content = f.read()
    assert "fifo_queue" in content


def test_webhook_queue_name_ends_with_fifo():
    """Verify webhook queue name ends with .fifo suffix."""
    sqs_file = AGENTS_SRC / "sqs.tf"
    with open(sqs_file, encoding="utf-8") as f:
        content = f.read()
    assert "${local.webhook_queue_name}.fifo" in content


def test_webhook_queue_has_content_deduplication():
    """Verify webhook queue has content-based deduplication enabled."""
    sqs_file = AGENTS_SRC / "sqs.tf"
    with open(sqs_file, encoding="utf-8") as f:
        content = f.read()
    assert "content_based_deduplication" in content


def test_webhook_dlq_is_fifo():
    """Verify webhook DLQ is also configured as FIFO (required for FIFO source)."""
    sqs_file = AGENTS_SRC / "sqs.tf"
    with open(sqs_file, encoding="utf-8") as f:
        content = f.read()
    # DLQ must also be FIFO when main queue is FIFO (using variable interpolation)
    assert "${local.webhook_queue_name}-dlq.fifo" in content
