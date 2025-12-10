"""Pytest fixtures for pre-deployment integration tests."""
import subprocess
from pathlib import Path

import boto3
import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
WWW_SHARED_DIR = REPO_ROOT / "src" / "www" / "shared"


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
def s3_client(aws_region):
    """Create an S3 client."""
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(scope="session")
def cloudfront_client(aws_region):
    """Create a CloudFront client."""
    return boto3.client("cloudfront", region_name=aws_region)


@pytest.fixture(scope="session")
def www_shared_terraform_initialized():
    """Initialize terraform for www_shared state access."""
    return _terraform_init(WWW_SHARED_DIR)


@pytest.fixture(scope="session")
def www_shared_outputs(request):
    """Get www_shared terraform outputs."""
    if not request.getfixturevalue("www_shared_terraform_initialized"):
        pytest.skip("Terraform init failed for www_shared")
    return {
        "bucket_name": _terraform_output(
            WWW_SHARED_DIR, "bucket_name"
        ),
        "bucket_arn": _terraform_output(
            WWW_SHARED_DIR, "bucket_arn"
        ),
        "website_domain_name": _terraform_output(
            WWW_SHARED_DIR, "website_domain_name"
        ),
        "cloudfront_distribution_id": _terraform_output(
            WWW_SHARED_DIR, "cloudfront_distribution_id"
        ),
    }
