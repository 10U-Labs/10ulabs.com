"""Pytest fixtures for pre-deployment integration tests."""
import subprocess
from pathlib import Path

import boto3
import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
BOOTSTRAP_DIR = REPO_ROOT / "src" / "bootstrap"


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


@pytest.fixture(scope="session")
def aws_region():
    """Provide the AWS region."""
    return "us-east-1"


@pytest.fixture(scope="session")
def s3_client(request):
    """Create an S3 client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("s3", region_name=region)


@pytest.fixture(scope="session")
def iam_client(request):
    """Create an IAM client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("iam", region_name=region)


@pytest.fixture(scope="session")
def route53_client(request):
    """Create a Route53 client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("route53", region_name=region)


@pytest.fixture(scope="session")
def terraform_initialized():
    """Initialize terraform for bootstrap state access."""
    return _terraform_init(BOOTSTRAP_DIR)


@pytest.fixture(scope="session")
def bootstrap_outputs(request):
    """Get bootstrap terraform outputs."""
    if not request.getfixturevalue("terraform_initialized"):
        pytest.skip("Terraform init failed for bootstrap")
    return {
        "state_bucket_name": _terraform_output(BOOTSTRAP_DIR, "state_bucket_name"),
        "github_actions_role_arn": _terraform_output(BOOTSTRAP_DIR, "github_actions_role_arn"),
        "route53_zone_id": _terraform_output(BOOTSTRAP_DIR, "route53_zone_id"),
    }
