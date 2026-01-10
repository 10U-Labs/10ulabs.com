"""Unit tests for ECS runner sqs.tf configuration."""


def test_sqs_file_exists(ecs_runner_src_dir):
    """Verify sqs.tf file exists."""
    assert (ecs_runner_src_dir / "sqs.tf").exists()


def test_sqs_dlq_resource_exists(ecs_runner_src_dir):
    """Verify SQS dead letter queue resource is defined."""
    content = (ecs_runner_src_dir / "sqs.tf").read_text()
    assert 'resource "aws_sqs_queue" "dlq"' in content


def test_sqs_dlq_has_name(ecs_runner_src_dir):
    """Verify DLQ has name configured."""
    content = (ecs_runner_src_dir / "sqs.tf").read_text()
    assert "module.common.lambda_handler_names.ecs_runner" in content


def test_sqs_dlq_retention_14_days(ecs_runner_src_dir):
    """Verify DLQ has 14 day message retention."""
    content = (ecs_runner_src_dir / "sqs.tf").read_text()
    assert "message_retention_seconds = 1209600" in content


def test_sqs_dlq_has_tags(ecs_runner_src_dir):
    """Verify DLQ has tags configured."""
    content = (ecs_runner_src_dir / "sqs.tf").read_text()
    assert 'Purpose   = "ecs-runner"' in content


def test_sqs_main_queue_resource_exists(ecs_runner_src_dir):
    """Verify main SQS queue resource is defined."""
    content = (ecs_runner_src_dir / "sqs.tf").read_text()
    assert 'resource "aws_sqs_queue" "main"' in content


def test_sqs_main_queue_visibility_timeout(ecs_runner_src_dir):
    """Verify main queue has visibility timeout configured."""
    content = (ecs_runner_src_dir / "sqs.tf").read_text()
    assert "visibility_timeout_seconds = 180" in content


def test_sqs_main_queue_message_retention(ecs_runner_src_dir):
    """Verify main queue has message retention configured."""
    content = (ecs_runner_src_dir / "sqs.tf").read_text()
    assert "message_retention_seconds  = 14400" in content


def test_sqs_main_queue_has_redrive_policy(ecs_runner_src_dir):
    """Verify main queue has redrive policy."""
    content = (ecs_runner_src_dir / "sqs.tf").read_text()
    assert "redrive_policy = jsonencode({" in content


def test_sqs_main_queue_redrive_references_dlq(ecs_runner_src_dir):
    """Verify redrive policy references DLQ."""
    content = (ecs_runner_src_dir / "sqs.tf").read_text()
    assert "deadLetterTargetArn = aws_sqs_queue.dlq.arn" in content


def test_sqs_main_queue_max_receive_count(ecs_runner_src_dir):
    """Verify redrive policy has max receive count of 3."""
    content = (ecs_runner_src_dir / "sqs.tf").read_text()
    assert "maxReceiveCount     = 3" in content


def test_sqs_queue_policy_resource_exists(ecs_runner_src_dir):
    """Verify SQS queue policy resource is defined."""
    content = (ecs_runner_src_dir / "sqs.tf").read_text()
    assert 'resource "aws_sqs_queue_policy" "api_gateway"' in content


def test_sqs_queue_policy_references_main_queue(ecs_runner_src_dir):
    """Verify queue policy references main queue."""
    content = (ecs_runner_src_dir / "sqs.tf").read_text()
    assert "queue_url = aws_sqs_queue.main.id" in content


def test_sqs_queue_policy_allows_api_gateway(ecs_runner_src_dir):
    """Verify queue policy allows API Gateway service."""
    content = (ecs_runner_src_dir / "sqs.tf").read_text()
    assert 'Service = "apigateway.amazonaws.com"' in content


def test_sqs_queue_policy_allows_send_message(ecs_runner_src_dir):
    """Verify queue policy allows sqs:SendMessage action."""
    content = (ecs_runner_src_dir / "sqs.tf").read_text()
    assert 'Action   = "sqs:SendMessage"' in content


def test_sqs_queue_policy_has_source_arn_condition(ecs_runner_src_dir):
    """Verify queue policy has source ARN condition."""
    content = (ecs_runner_src_dir / "sqs.tf").read_text()
    assert "ArnLike = {" in content


def test_sqs_queue_policy_condition_specifies_post_runners_ecs(ecs_runner_src_dir):
    """Verify queue policy condition specifies POST /v1/runners/ecs."""
    content = (ecs_runner_src_dir / "sqs.tf").read_text()
    assert "POST/v1/runners/ecs" in content
