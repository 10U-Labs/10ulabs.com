"""Pytest fixtures for pre-deployment integration tests."""
import subprocess
from pathlib import Path

import boto3
import pytest


REPO_ROOT = Path(__file__).resolve().parents[6]
IMAGE_FOR_EC2_RUNNERS_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "image_for_ec2_runners"
RUNNERS_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "runners"


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
def image_for_ec2_runners_terraform_initialized():
    """Initialize terraform for image_for_ec2_runners state access."""
    return _terraform_init(IMAGE_FOR_EC2_RUNNERS_DIR)


@pytest.fixture(scope="session")
def runners_terraform_initialized():
    """Initialize terraform for runners state access."""
    return _terraform_init(RUNNERS_DIR)


@pytest.fixture(scope="session")
def image_for_ec2_runners_outputs(request):
    """Get image_for_ec2_runners terraform outputs."""
    if not request.getfixturevalue("image_for_ec2_runners_terraform_initialized"):
        pytest.skip("Terraform init failed for image_for_ec2_runners")
    return {
        "lambda_function_arn": _terraform_output(
            IMAGE_FOR_EC2_RUNNERS_DIR, "lambda_function_arn"
        ),
        "lambda_function_name": _terraform_output(
            IMAGE_FOR_EC2_RUNNERS_DIR, "lambda_function_name"
        ),
        "lambda_invoke_arn": _terraform_output(
            IMAGE_FOR_EC2_RUNNERS_DIR, "lambda_invoke_arn"
        ),
    }


@pytest.fixture(scope="session")
def runners_outputs(request):
    """Get runners terraform outputs."""
    if not request.getfixturevalue("runners_terraform_initialized"):
        pytest.skip("Terraform init failed for runners")
    return {
        "vpc_id": _terraform_output(RUNNERS_DIR, "vpc_id"),
        "vpc_public_subnet_ids": _terraform_output(
            RUNNERS_DIR, "vpc_public_subnet_ids"
        ),
        "runner_security_group_id": _terraform_output(
            RUNNERS_DIR, "runner_security_group_id"
        ),
    }
