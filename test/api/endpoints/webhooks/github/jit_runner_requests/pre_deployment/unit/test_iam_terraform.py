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
