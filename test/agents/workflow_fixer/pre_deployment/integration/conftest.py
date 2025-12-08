"""Pytest fixtures for workflow_fixer pre-deployment integration tests."""

import boto3
import pytest


AWS_REGION = "us-east-2"
STATE_BUCKET = "10ulabs-terraform-state-us-east-2"
SSM_GITHUB_PAT = "/TenULabs/github_pat"


@pytest.fixture(scope="session")
def sts_client():
    """Create an STS client."""
    return boto3.client("sts", region_name=AWS_REGION)


@pytest.fixture(scope="session")
def iam_client():
    """Create an IAM client."""
    return boto3.client("iam", region_name=AWS_REGION)


@pytest.fixture(scope="session")
def s3_client():
    """Create an S3 client."""
    return boto3.client("s3", region_name=AWS_REGION)


@pytest.fixture(scope="session")
def ssm_client():
    """Create an SSM client."""
    return boto3.client("ssm", region_name=AWS_REGION)


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
def state_bucket_name():
    """Provide the terraform state bucket name."""
    return STATE_BUCKET


@pytest.fixture(scope="session")
def ssm_github_pat_name():
    """Provide the SSM parameter name for GitHub PAT."""
    return SSM_GITHUB_PAT
