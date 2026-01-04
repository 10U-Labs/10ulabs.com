"""Pytest fixtures for runners post-deployment integration tests.

Post-Deployment Layers:
- Layer 1: Existence - Deployed resources exist
- Layer 2: Configuration - Deployed resources configured correctly
- Layer 3: Wiring - Components connected properly
"""
import json

import boto3
import pytest

from repo_utils import REPO_ROOT
from terraform_config import TEST_AWS_REGION, get_shared_config
from test_fixtures.aws import get_log_group_info
from test_fixtures.terraform import terraform_init, terraform_output

RUNNERS_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "runners"


@pytest.fixture(scope="session")
def aws_region():
    """Provide the AWS region."""
    return TEST_AWS_REGION


@pytest.fixture(scope="session")
def runners_initialized():
    """Verify terraform init succeeds for runners."""
    return terraform_init(RUNNERS_DIR)


@pytest.fixture(scope="session")
def lambda_function_name(request):
    """Get the Lambda function name from terraform outputs."""
    initialized = request.getfixturevalue("runners_initialized")
    if not initialized:
        pytest.skip("Terraform init failed for runners")
    return terraform_output(RUNNERS_DIR, "lambda_function_name")


@pytest.fixture(scope="session")
def lambda_function_arn(request):
    """Get the Lambda function ARN from terraform outputs."""
    initialized = request.getfixturevalue("runners_initialized")
    if not initialized:
        pytest.skip("Terraform init failed for runners")
    return terraform_output(RUNNERS_DIR, "lambda_function_arn")


@pytest.fixture(scope="session")
def sqs_queue_url(request):
    """Get the SQS queue URL from terraform outputs."""
    initialized = request.getfixturevalue("runners_initialized")
    if not initialized:
        pytest.skip("Terraform init failed for runners")
    return terraform_output(RUNNERS_DIR, "sqs_queue_url")


@pytest.fixture(scope="session")
def sqs_queue_arn(request):
    """Get the SQS queue ARN from terraform outputs."""
    initialized = request.getfixturevalue("runners_initialized")
    if not initialized:
        pytest.skip("Terraform init failed for runners")
    return terraform_output(RUNNERS_DIR, "sqs_queue_arn")


@pytest.fixture(scope="session")
def sqs_dlq_name(request):
    """Get the SQS DLQ name from terraform outputs."""
    initialized = request.getfixturevalue("runners_initialized")
    if not initialized:
        pytest.skip("Terraform init failed for runners")
    return terraform_output(RUNNERS_DIR, "sqs_dlq_name")


@pytest.fixture(scope="session")
def sqs_dlq_arn(request):
    """Get the SQS DLQ ARN from terraform outputs."""
    initialized = request.getfixturevalue("runners_initialized")
    if not initialized:
        pytest.skip("Terraform init failed for runners")
    return terraform_output(RUNNERS_DIR, "sqs_dlq_arn")


@pytest.fixture(scope="session")
def lambda_role_name(request):
    """Extract Lambda role name from naming convention."""
    # Role name is FunctionName + "Role"
    func_name = request.getfixturevalue("lambda_function_name")
    return f"{func_name}Role"


@pytest.fixture(scope="session")
def lambda_role_arn(request):
    """Get the full ARN for the Lambda execution role."""
    role_name = request.getfixturevalue("lambda_role_name")
    config = request.getfixturevalue("shared_config")
    account_id = config.get("aws_account_id", "")
    return f"arn:aws:iam::{account_id}:role/{role_name}"


@pytest.fixture(scope="module")
def handler_log_group(request):
    """Get the Lambda handler log group info from CloudWatch."""
    func_name = request.getfixturevalue("lambda_function_name")
    client = request.getfixturevalue("logs_client")
    log_group_name = f"/aws/lambda/{func_name}"
    return get_log_group_info(client, log_group_name)


@pytest.fixture(scope="session")
def sts_client():
    """Create an STS client."""
    return boto3.client("sts", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def iam_client():
    """Create an IAM client."""
    return boto3.client("iam", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def s3_client():
    """Create an S3 client."""
    return boto3.client("s3", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def lambda_client():
    """Create a Lambda client."""
    return boto3.client("lambda", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def sqs_client():
    """Create an SQS client."""
    return boto3.client("sqs", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def logs_client():
    """Create a CloudWatch Logs client."""
    return boto3.client("logs", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def kms_client():
    """Create a KMS client."""
    return boto3.client("kms", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def shared_config():
    """Get shared config."""
    return get_shared_config()


@pytest.fixture(scope="session")
def sqs_redrive_policy(request):
    """Get the SQS redrive policy as a dict."""
    client = request.getfixturevalue("sqs_client")
    queue_url = request.getfixturevalue("sqs_queue_url")
    if not queue_url:
        return None
    response = client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=["RedrivePolicy"]
    )
    policy_str = response.get("Attributes", {}).get("RedrivePolicy", "")
    if not policy_str:
        return None
    return json.loads(policy_str)


@pytest.fixture(scope="module")
def sqs_event_source_mapping(request):
    """Get the first SQS event source mapping for the Lambda."""
    from botocore.exceptions import ClientError
    client = request.getfixturevalue("lambda_client")
    func_name = request.getfixturevalue("lambda_function_name")
    queue_arn = request.getfixturevalue("sqs_queue_arn")
    if not func_name or not queue_arn:
        return None
    try:
        response = client.list_event_source_mappings(
            FunctionName=func_name,
            EventSourceArn=queue_arn
        )
        mappings = response.get("EventSourceMappings", [])
        return mappings[0] if mappings else None
    except ClientError:
        return None
