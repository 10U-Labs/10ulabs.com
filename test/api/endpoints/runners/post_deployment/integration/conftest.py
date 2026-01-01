"""Pytest fixtures for runners post-deployment integration tests.

Post-Deployment Layers:
- Layer 1: Existence - Deployed resources exist
- Layer 2: Configuration - Deployed resources configured correctly
- Layer 3: Wiring - Components connected properly
"""
import pytest

from repo_utils import REPO_ROOT
from terraform_config import TEST_AWS_REGION
from test_fixtures.aws import get_log_group_info
from test_fixtures.terraform import terraform_init, terraform_output

pytest_plugins = ['pytest_layers']


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
def lambda_function_name(runners_initialized):
    """Get the Lambda function name from terraform outputs."""
    if not runners_initialized:
        pytest.skip("Terraform init failed for runners")
    return terraform_output(RUNNERS_DIR, "lambda_function_name")


@pytest.fixture(scope="session")
def lambda_function_arn(runners_initialized):
    """Get the Lambda function ARN from terraform outputs."""
    if not runners_initialized:
        pytest.skip("Terraform init failed for runners")
    return terraform_output(RUNNERS_DIR, "lambda_function_arn")


@pytest.fixture(scope="session")
def sqs_queue_url(runners_initialized):
    """Get the SQS queue URL from terraform outputs."""
    if not runners_initialized:
        pytest.skip("Terraform init failed for runners")
    return terraform_output(RUNNERS_DIR, "sqs_queue_url")


@pytest.fixture(scope="session")
def sqs_queue_arn(runners_initialized):
    """Get the SQS queue ARN from terraform outputs."""
    if not runners_initialized:
        pytest.skip("Terraform init failed for runners")
    return terraform_output(RUNNERS_DIR, "sqs_queue_arn")


@pytest.fixture(scope="session")
def sqs_dlq_name(runners_initialized):
    """Get the SQS DLQ name from terraform outputs."""
    if not runners_initialized:
        pytest.skip("Terraform init failed for runners")
    return terraform_output(RUNNERS_DIR, "sqs_dlq_name")


@pytest.fixture(scope="session")
def sqs_dlq_arn(runners_initialized):
    """Get the SQS DLQ ARN from terraform outputs."""
    if not runners_initialized:
        pytest.skip("Terraform init failed for runners")
    return terraform_output(RUNNERS_DIR, "sqs_dlq_arn")


@pytest.fixture(scope="session")
def lambda_role_name(lambda_function_name):
    """Extract Lambda role name from naming convention."""
    # Role name is FunctionName + "Role"
    return f"{lambda_function_name}Role"


@pytest.fixture(scope="session")
def lambda_role_arn(lambda_role_name, shared_config):
    """Get the full ARN for the Lambda execution role."""
    account_id = shared_config.get("aws_account_id", "")
    return f"arn:aws:iam::{account_id}:role/{lambda_role_name}"


@pytest.fixture(scope="module")
def handler_log_group(lambda_function_name, logs_client):
    """Get the Lambda handler log group info from CloudWatch."""
    log_group_name = f"/aws/lambda/{lambda_function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(scope="session")
def sts_client():
    """Create an STS client."""
    import boto3
    return boto3.client("sts", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def iam_client():
    """Create an IAM client."""
    import boto3
    return boto3.client("iam", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def s3_client():
    """Create an S3 client."""
    import boto3
    return boto3.client("s3", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def lambda_client():
    """Create a Lambda client."""
    import boto3
    return boto3.client("lambda", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def sqs_client():
    """Create an SQS client."""
    import boto3
    return boto3.client("sqs", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def logs_client():
    """Create a CloudWatch Logs client."""
    import boto3
    return boto3.client("logs", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def kms_client():
    """Create a KMS client."""
    import boto3
    return boto3.client("kms", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def shared_config():
    """Get shared config."""
    from terraform_config import get_shared_config
    return get_shared_config()
