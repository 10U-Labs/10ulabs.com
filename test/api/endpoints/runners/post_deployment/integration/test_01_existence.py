"""Layer 1: Existence tests.

Verify resources created by this deployment exist.
"""
import pytest
from botocore.exceptions import ClientError

pytestmark = pytest.mark.layer(1)


def test_lambda_function_exists(lambda_client, lambda_function_name):
    """Verify the runners router Lambda function exists."""
    if not lambda_function_name:
        pytest.skip("lambda_function_name not available from terraform output")
    try:
        response = lambda_client.get_function(FunctionName=lambda_function_name)
        assert response["Configuration"]["FunctionName"] == lambda_function_name
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            pytest.fail(
                f"Lambda function '{lambda_function_name}' does not exist. "
                "Run terraform apply in src/api/endpoints/runners/"
            )
        raise


def test_lambda_execution_role_exists(iam_client, lambda_role_name):
    """Verify the Lambda execution role exists."""
    try:
        response = iam_client.get_role(RoleName=lambda_role_name)
        assert response.get("Role") is not None
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            pytest.fail(
                f"Lambda execution role '{lambda_role_name}' does not exist. "
                "Run terraform apply in src/api/endpoints/runners/"
            )
        raise


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
