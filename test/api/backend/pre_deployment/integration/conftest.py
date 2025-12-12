"""Pytest fixtures for api_backend pre-deployment integration tests."""

import re

from test.api.conftest import REPO_ROOT, terraform_init, terraform_output

import boto3
import pytest


BOOTSTRAP_DIR = REPO_ROOT / "src" / "bootstrap"

STATE_BUCKET = "10ulabs-terraform-state-us-east-2"
STATE_REGION = "us-east-2"


@pytest.fixture(scope="session")
def sts_client():
    """Create an STS client."""
    return boto3.client("sts", region_name=STATE_REGION)


@pytest.fixture(scope="session")
def iam_client():
    """Create an IAM client."""
    return boto3.client("iam", region_name=STATE_REGION)


@pytest.fixture(scope="session")
def caller_identity(request):
    """Get the current caller identity."""
    sts = request.getfixturevalue("sts_client")
    return sts.get_caller_identity()


@pytest.fixture(scope="session")
def current_role_arn(request):
    """Extract the role ARN from caller identity."""
    identity = request.getfixturevalue("caller_identity")
    arn = identity.get("Arn", "")
    # Convert assumed-role ARN to role ARN
    # arn:aws:sts::123:assumed-role/role-name/session -> arn:aws:iam::123:role/role-name
    if ":assumed-role/" in arn:
        account = identity.get("Account", "")
        role_name = arn.split("/")[1]
        return f"arn:aws:iam::{account}:role/{role_name}"
    return arn


@pytest.fixture(scope="session")
def current_role_name(request):
    """Extract the role name from the role ARN."""
    role_arn = request.getfixturevalue("current_role_arn")
    if not role_arn:
        return ""
    return role_arn.split("/")[-1]


@pytest.fixture(scope="session")
def state_bucket_name():
    """Provide the terraform state bucket name."""
    return STATE_BUCKET


@pytest.fixture(scope="session")
def state_bucket_region():
    """Provide the terraform state bucket region."""
    return STATE_REGION


@pytest.fixture(scope="session")
def s3_client():
    """Create an S3 client for the state bucket region."""
    return boto3.client("s3", region_name=STATE_REGION)


@pytest.fixture(scope="session")
def bootstrap_initialized():
    """Initialize terraform for bootstrap state access."""
    return terraform_init(BOOTSTRAP_DIR)


@pytest.fixture(scope="session")
def bootstrap_outputs(request):
    """Get bootstrap terraform outputs."""
    if not request.getfixturevalue("bootstrap_initialized"):
        pytest.skip("Terraform init failed for bootstrap")
    return {
        "arn_for_central_logs_bucket": terraform_output(
            BOOTSTRAP_DIR, "arn_for_central_logs_bucket"
        ),
        "arn_for_github_actions_role": terraform_output(
            BOOTSTRAP_DIR, "arn_for_github_actions_role"
        ),
        "arn_for_state_bucket": terraform_output(
            BOOTSTRAP_DIR, "arn_for_state_bucket"
        ),
    }


@pytest.fixture(scope="session")
def central_logs_bucket_name(request):
    """Extract the central logs bucket name from its ARN."""
    outputs = request.getfixturevalue("bootstrap_outputs")
    arn = outputs.get("arn_for_central_logs_bucket", "")
    if not arn:
        return ""
    match = re.match(r"arn:aws:s3:::(.+)$", arn)
    return match.group(1) if match else ""
