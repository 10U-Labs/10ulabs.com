"""Pytest fixtures for api/shared/runners pre-deployment integration tests.

These tests follow the 5-layer testing model from PRE_DEPLOYMENT_INTEGRATION_TESTS.md:
- Layer 1: Authentication - Are AWS credentials configured and valid?
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: Existence - Do the required resources exist?
- Layer 4: Configuration - Are resources configured correctly?
- Layer 5: Capability - Can we perform required operations?
"""

import boto3
import pytest
from repo_utils import REPO_ROOT


API_SHARED_RUNNERS_SRC = REPO_ROOT / "src" / "api" / "shared" / "runners"

STATE_BUCKET = "10ulabs-terraform-state-us-east-2"
STATE_REGION = "us-east-2"
STATE_KEY = "api/shared/runners/terraform.tfstate"


@pytest.fixture(scope="session")
def sts_client():
    """Create an STS client."""
    return boto3.client("sts", region_name=STATE_REGION)


@pytest.fixture(scope="session")
def iam_client():
    """Create an IAM client."""
    return boto3.client("iam", region_name=STATE_REGION)


@pytest.fixture(scope="session")
def s3_client():
    """Create an S3 client for the state bucket region."""
    return boto3.client("s3", region_name=STATE_REGION)


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
def runners_state_key():
    """Provide the terraform state key for api_shared_runners."""
    return STATE_KEY


@pytest.fixture(scope="session")
def api_shared_runners_src():
    """Provide path to api_shared_runners source directory."""
    return API_SHARED_RUNNERS_SRC
