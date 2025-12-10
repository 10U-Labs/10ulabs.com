"""Pytest fixtures for pre-deployment integration tests."""
import subprocess
from pathlib import Path

import boto3
import pytest


REPO_ROOT = Path(__file__).resolve().parents[6]
IMAGE_FOR_ECS_RUNNERS_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "image_for_ecs_runners"
API_SHARED_ECR_DIR = REPO_ROOT / "src" / "api" / "shared" / "ecs_runner"
RUNNERS_DIR = REPO_ROOT / "src" / "api" / "shared" / "runners"


def _terraform_init(directory: Path) -> bool:
    """Initialize terraform in the given directory."""
    result = subprocess.run(
        ["terraform", "init", "-backend=true", "-input=false"],
        cwd=str(directory),
        capture_output=True,
        text=True,
        check=False
    )
    if result.returncode != 0:
        print(f"terraform init failed in {directory}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
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
    if result.returncode != 0:
        print(f"terraform output {name} failed in {directory}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
    return result.stdout.strip() if result.returncode == 0 else ""


@pytest.fixture(scope="session")
def ec2_client(shared_config):
    """Create an EC2 client."""
    return boto3.client("ec2", region_name=shared_config["aws_region"])


@pytest.fixture(scope="session")
def image_for_ecs_runners_terraform_initialized():
    """Initialize terraform for image_for_ecs_runners state access."""
    return _terraform_init(IMAGE_FOR_ECS_RUNNERS_DIR)


@pytest.fixture(scope="session")
def api_shared_ecr_terraform_initialized():
    """Initialize terraform for api_shared_ecr state access."""
    return _terraform_init(API_SHARED_ECR_DIR)


@pytest.fixture(scope="session")
def runners_terraform_initialized():
    """Initialize terraform for runners state access."""
    return _terraform_init(RUNNERS_DIR)


@pytest.fixture(scope="session")
def image_for_ecs_runners_outputs(request):
    """Get image_for_ecs_runners terraform outputs."""
    if not request.getfixturevalue("image_for_ecs_runners_terraform_initialized"):
        pytest.skip("Terraform init failed for image_for_ecs_runners")
    return {
        "lambda_function_arn": _terraform_output(
            IMAGE_FOR_ECS_RUNNERS_DIR, "lambda_function_arn"
        ),
        "lambda_function_name": _terraform_output(
            IMAGE_FOR_ECS_RUNNERS_DIR, "lambda_function_name"
        ),
        "lambda_invoke_arn": _terraform_output(
            IMAGE_FOR_ECS_RUNNERS_DIR, "lambda_invoke_arn"
        ),
    }


@pytest.fixture(scope="session")
def api_shared_ecr_outputs(request):
    """Get api_shared_ecr terraform outputs."""
    if not request.getfixturevalue("api_shared_ecr_terraform_initialized"):
        pytest.skip("Terraform init failed for api_shared_ecr")
    return {
        "repository_name": _terraform_output(
            API_SHARED_ECR_DIR, "ecr_repository_name"
        ),
        "repository_url": _terraform_output(
            API_SHARED_ECR_DIR, "ecr_repository_url"
        ),
        "repository_arn": _terraform_output(
            API_SHARED_ECR_DIR, "ecr_repository_arn"
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
