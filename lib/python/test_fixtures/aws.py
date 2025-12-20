"""AWS fixtures for pytest tests.

Use by adding to conftest.py:
    pytest_plugins = ['test_fixtures.aws']
"""
import boto3
import pytest
from terraform_config import get_shared_config


@pytest.fixture(scope="session")
def shared_config():
    """Provide parsed configuration from the shared Terraform module."""
    return get_shared_config()


@pytest.fixture(scope="session")
def aws_region(shared_config):
    """Provide the AWS region from shared config."""
    return shared_config["aws_region"]


@pytest.fixture(scope="session")
def ssm_github_pat_name(shared_config):
    """Provide the SSM parameter name for GitHub PAT."""
    return shared_config["ssm_github_pat_name"]


@pytest.fixture(scope="session")
def state_bucket_name(shared_config):
    """Provide the Terraform state bucket name."""
    return shared_config["name_for_terraform_state_bucket"]


@pytest.fixture(scope="session")
def sts_client(aws_region):
    """Create an STS client."""
    return boto3.client("sts", region_name=aws_region)


@pytest.fixture(scope="session")
def iam_client(aws_region):
    """Create an IAM client."""
    return boto3.client("iam", region_name=aws_region)


@pytest.fixture(scope="session")
def s3_client(aws_region):
    """Create an S3 client."""
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(scope="session")
def ssm_client(aws_region):
    """Create an SSM client."""
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(scope="session")
def kms_client(aws_region):
    """Create a KMS client."""
    return boto3.client("kms", region_name=aws_region)


@pytest.fixture(scope="session")
def ecr_client(aws_region):
    """Create an ECR client."""
    return boto3.client("ecr", region_name=aws_region)


@pytest.fixture(scope="session")
def caller_identity(sts_client):
    """Get the current caller identity."""
    return sts_client.get_caller_identity()


@pytest.fixture(scope="session")
def current_role_arn(caller_identity):
    """Extract the role ARN from caller identity."""
    arn = caller_identity.get("Arn", "")
    # Convert assumed-role ARN to role ARN
    # arn:aws:sts::123:assumed-role/role-name/session -> arn:aws:iam::123:role/role-name
    if ":assumed-role/" in arn:
        account = caller_identity.get("Account", "")
        role_name = arn.split("/")[1]
        return f"arn:aws:iam::{account}:role/{role_name}"
    return arn


@pytest.fixture(scope="session")
def current_role_name(current_role_arn):
    """Extract the role name from the role ARN."""
    if not current_role_arn:
        return ""
    return current_role_arn.split("/")[-1]


@pytest.fixture(scope="session")
def ecr_repository_name(shared_config):
    """Provide the ECR repository name for agents."""
    return shared_config["ecr_repository_name_agents"]
