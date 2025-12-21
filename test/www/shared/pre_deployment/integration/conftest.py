"""Pytest fixtures for pre-deployment integration tests."""
import subprocess
from pathlib import Path

import boto3
import pytest
from repo_utils import REPO_ROOT

pytest_plugins = ['pytest_layers']


BOOTSTRAP_DIR = REPO_ROOT / "src" / "bootstrap"
AWS_REGION_VALUE = "us-east-2"


def _terraform_init(directory: Path) -> bool:
    """Initialize terraform in the given directory."""
    result = subprocess.run(
        ["terraform", "init", "-backend=true", "-input=false"],
        cwd=str(directory),
        capture_output=True,
        text=True,
        check=False
    )
    return result.returncode == 0


def _terraform_output(directory: Path, name: str) -> str:
    """Get a terraform output value."""
    cmd = ["terraform", "output", "-raw", name]
    result = subprocess.run(
        cmd,
        cwd=str(directory),
        capture_output=True,
        text=True,
        check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _get_bootstrap_outputs() -> dict:
    """Get all bootstrap terraform outputs."""
    if not _terraform_init(BOOTSTRAP_DIR):
        return {}
    return {
        "state_bucket_arn": _terraform_output(
            BOOTSTRAP_DIR, "arn_for_state_bucket"
        ),
        "github_actions_role_arn": _terraform_output(
            BOOTSTRAP_DIR, "arn_for_github_actions_role"
        ),
        "github_actions_role_name": _terraform_output(
            BOOTSTRAP_DIR, "name_for_github_actions_role"
        ),
        "hosted_zone_id": _terraform_output(
            BOOTSTRAP_DIR, "hosted_zone_id"
        ),
    }


@pytest.fixture(scope="session")
def aws_region():
    """Provide the AWS region."""
    return AWS_REGION_VALUE


@pytest.fixture(scope="session")
def s3_client():
    """Create an S3 client."""
    return boto3.client("s3", region_name=AWS_REGION_VALUE)


@pytest.fixture(scope="session")
def iam_client():
    """Create an IAM client."""
    return boto3.client("iam", region_name=AWS_REGION_VALUE)


@pytest.fixture(scope="session")
def route53_client():
    """Create a Route53 client."""
    return boto3.client("route53", region_name=AWS_REGION_VALUE)


@pytest.fixture(scope="session")
def sts_client():
    """Create an STS client."""
    return boto3.client("sts", region_name=AWS_REGION_VALUE)


@pytest.fixture(scope="session")
def bootstrap_outputs():
    """Get bootstrap terraform outputs."""
    outputs = _get_bootstrap_outputs()
    if not outputs:
        pytest.skip("Terraform init failed for bootstrap")
    return outputs


@pytest.fixture(scope="session")
def state_bucket_name(request):
    """Extract state bucket name from ARN."""
    outputs = request.getfixturevalue("bootstrap_outputs")
    arn = outputs.get("state_bucket_arn", "")
    if not arn:
        pytest.skip("state_bucket_arn not found in bootstrap outputs")
    return arn.split(":")[-1]


@pytest.fixture(scope="session")
def github_actions_role_arn(request):
    """Get GitHub Actions role ARN."""
    outputs = request.getfixturevalue("bootstrap_outputs")
    arn = outputs.get("github_actions_role_arn", "")
    if not arn:
        pytest.skip("github_actions_role_arn not found in bootstrap outputs")
    return arn


@pytest.fixture(scope="session")
def github_actions_role_name(request):
    """Get GitHub Actions role name."""
    outputs = request.getfixturevalue("bootstrap_outputs")
    name = outputs.get("github_actions_role_name", "")
    if not name:
        pytest.skip("github_actions_role_name not found in bootstrap outputs")
    return name


@pytest.fixture(scope="session")
def hosted_zone_id(request):
    """Get Route53 hosted zone ID."""
    outputs = request.getfixturevalue("bootstrap_outputs")
    zone_id = outputs.get("hosted_zone_id", "")
    if not zone_id:
        pytest.skip("hosted_zone_id not found in bootstrap outputs")
    return zone_id


@pytest.fixture(scope="session")
def current_identity(request):
    """Get the current AWS identity."""
    client = request.getfixturevalue("sts_client")
    return client.get_caller_identity()
