"""Pytest fixtures for pre-deployment integration tests."""
import subprocess
from pathlib import Path

import boto3
import pytest


REPO_ROOT = Path(__file__).resolve().parents[6]
ENDPOINT_HEALTH_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "health"


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
def ecr_client(request):
    """Create an ECR client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("ecr", region_name=region)


@pytest.fixture(scope="session")
def iam_client(request):
    """Create an IAM client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("iam", region_name=region)


@pytest.fixture(scope="session")
def terraform_initialized():
    """Initialize terraform for endpoint_health state access."""
    return _terraform_init(ENDPOINT_HEALTH_DIR)


@pytest.fixture(scope="session")
def endpoint_health_outputs(request):
    """Get endpoint_health terraform outputs."""
    if not request.getfixturevalue("terraform_initialized"):
        pytest.skip("Terraform init failed for endpoint_health")
    return {
        "health_endpoint_url": _terraform_output(ENDPOINT_HEALTH_DIR, "health_endpoint_url"),
    }


@pytest.fixture(scope="session")
def api_url(request):
    """Get the API URL from health endpoint."""
    outputs = request.getfixturevalue("endpoint_health_outputs")
    health_url = outputs.get("health_endpoint_url", "")
    if health_url:
        return health_url.rsplit("/health", 1)[0]
    return ""
