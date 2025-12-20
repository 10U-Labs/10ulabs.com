"""Unit tests for IAM terraform configuration."""


def test_iam_terraform_file_exists(runners_src_path):
    """Test iam terraform file exists."""
    iam_file = runners_src_path / "iam.tf"
    assert iam_file.exists()


def test_webhook_handler_sqs_policy_exists(runners_src_path):
    """Verify lambda_runners_handler_sqs policy exists."""
    iam_file = runners_src_path / "iam.tf"
    content = iam_file.read_text()

    assert 'resource "aws_iam_role_policy" "lambda_runners_handler_sqs"' in content


def test_webhook_handler_sqs_policy_covers_job_queue(runners_src_path):
    """Verify webhook handler IAM policy covers job queue ARN."""
    iam_file = runners_src_path / "iam.tf"
    content = iam_file.read_text()

    start = content.find('resource "aws_iam_role_policy" "lambda_runners_handler_sqs"')
    end = content.find('resource "aws_iam_role_policy"', start + 1)
    if end == -1:
        end = len(content)
    policy_block = content[start:end]

    assert "aws_sqs_queue.job_queue.arn" in policy_block


def test_webhook_handler_sqs_policy_grants_get_queue_attributes_on_job_queue(runners_src_path):
    """Verify webhook handler IAM policy grants GetQueueAttributes on job queue.

    The webhook_router.py code calls get_queue_attributes on the job queue
    to publish queue depth metrics. The IAM policy must grant this permission
    in the same statement that covers job_queue.
    """
    iam_file = runners_src_path / "iam.tf"
    content = iam_file.read_text()

    start = content.find('resource "aws_iam_role_policy" "lambda_runners_handler_sqs"')
    end = content.find('resource "aws_iam_role_policy"', start + 1)
    if end == -1:
        end = len(content)
    policy_block = content[start:end]

    job_queue_statement_start = policy_block.find("aws_sqs_queue.job_queue.arn")
    statement_start = policy_block.rfind("{", 0, job_queue_statement_start)
    statement_end = policy_block.find("}", job_queue_statement_start)
    statement_block = policy_block[statement_start:statement_end]

    assert "sqs:GetQueueAttributes" in statement_block, (
        "Statement covering job_queue missing sqs:GetQueueAttributes - "
        "webhook_router.py needs this to publish queue depth metrics"
    )


def test_webhook_handler_role_exists(runners_src_path):
    """Verify webhook handler IAM role is defined."""
    iam_file = runners_src_path / "iam.tf"
    content = iam_file.read_text()

    assert 'resource "aws_iam_role" "lambda_runners_handler"' in content


def test_webhook_handler_role_trusts_lambda_service(runners_src_path):
    """Verify webhook handler role trusts Lambda service."""
    iam_file = runners_src_path / "iam.tf"
    content = iam_file.read_text()

    start = content.find('resource "aws_iam_role" "lambda_runners_handler"')
    end = content.find("resource ", start + 1)
    role_block = content[start:end]

    assert "lambda.amazonaws.com" in role_block


def test_webhook_handler_role_allows_assume_role(runners_src_path):
    """Verify webhook handler role allows sts:AssumeRole."""
    iam_file = runners_src_path / "iam.tf"
    content = iam_file.read_text()

    start = content.find('resource "aws_iam_role" "lambda_runners_handler"')
    end = content.find("resource ", start + 1)
    role_block = content[start:end]

    assert "sts:AssumeRole" in role_block
