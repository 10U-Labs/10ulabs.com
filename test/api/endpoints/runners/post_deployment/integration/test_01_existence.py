"""Layer 1: Existence tests.

Verify resources created by this deployment exist.
"""
import pytest

from test_fixtures.integration import check_iam_role_exists, check_lambda_function_exists


TERRAFORM_PATH = "src/api/endpoints/runners/"


def test_lambda_function_exists(lambda_client, lambda_function_name):
    """Verify the runners router Lambda function exists."""
    if not lambda_function_name:
        pytest.skip("lambda_function_name not available from terraform output")
    check_lambda_function_exists(lambda_client, lambda_function_name, TERRAFORM_PATH)


def test_lambda_execution_role_exists(iam_client, lambda_role_name):
    """Verify the Lambda execution role exists."""
    check_iam_role_exists(iam_client, lambda_role_name, TERRAFORM_PATH)


def test_sqs_queue_exists(sqs_client, sqs_queue_url):
    """Verify the SQS queue exists."""
    if not sqs_queue_url:
        pytest.skip("sqs_queue_url not available from terraform output")
    try:
        response = sqs_client.get_queue_attributes(
            QueueUrl=sqs_queue_url,
            AttributeNames=["QueueArn"]
        )
        assert response.get("Attributes", {}).get("QueueArn") is not None
    except ClientError as e:
        if e.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
            pytest.fail(
                f"SQS queue '{sqs_queue_url}' does not exist. "
                "Run terraform apply in src/api/endpoints/runners/"
            )
        raise


def test_sqs_dlq_exists(sqs_client, sqs_dlq_arn):
    """Verify the SQS dead-letter queue exists."""
    if not sqs_dlq_arn:
        pytest.skip("sqs_dlq_arn not available from terraform output")
    try:
        # Get DLQ URL from ARN
        dlq_name = sqs_dlq_arn.split(":")[-1]
        response = sqs_client.get_queue_url(QueueName=dlq_name)
        assert response.get("QueueUrl") is not None
    except ClientError as e:
        if e.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
            pytest.fail(
                f"SQS DLQ with ARN '{sqs_dlq_arn}' does not exist. "
                "Run terraform apply in src/api/endpoints/runners/"
            )
        raise


def test_handler_log_group_exists(handler_log_group):
    """Verify CloudWatch log group for Lambda handler exists."""
    assert handler_log_group["exists"], (
        f"CloudWatch log group '{handler_log_group['name']}' does not exist"
    )
