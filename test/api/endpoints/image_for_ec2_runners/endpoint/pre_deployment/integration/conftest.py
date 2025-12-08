"""Pytest fixtures for pre-deployment integration tests."""
import subprocess
from pathlib import Path

import boto3
import pytest


REPO_ROOT = Path(__file__).resolve().parents[8]
API_BACKEND_DIR = REPO_ROOT / "src" / "api" / "backend"


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
def ec2_client(request):
    """Create an EC2 client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("ec2", region_name=region)


@pytest.fixture(scope="session")
def terraform_initialized():
    """Initialize terraform for api_backend state access."""
    return _terraform_init(API_BACKEND_DIR)


@pytest.fixture(scope="session")
def api_backend_outputs(request):
    """Get api_backend terraform outputs."""
    if not request.getfixturevalue("terraform_initialized"):
        pytest.skip("Terraform init failed for api_backend")
    return {
        "ec2_runner_ami_purpose_value": _terraform_output(
            API_BACKEND_DIR, "ec2_runner_ami_purpose_value"
        ),
        "ec2_runner_ami_stable_tag": _terraform_output(
            API_BACKEND_DIR, "ec2_runner_ami_stable_tag"
        ),
    }


@pytest.fixture(scope="session")
def ami_purpose_value(request):
    """Get the AMI purpose tag value."""
    outputs = request.getfixturevalue("api_backend_outputs")
    return outputs.get("ec2_runner_ami_purpose_value", "")


@pytest.fixture(scope="session")
def ami_stable_tag(request):
    """Get the AMI stable tag name."""
    outputs = request.getfixturevalue("api_backend_outputs")
    return outputs.get("ec2_runner_ami_stable_tag", "")
