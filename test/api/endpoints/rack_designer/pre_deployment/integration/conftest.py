"""Pytest fixtures for pre-deployment integration tests."""
import subprocess
from pathlib import Path

import boto3
import pytest


REPO_ROOT = Path(__file__).resolve().parents[6]
ECS_RUNNER_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "ecs_runner"
API_BACKEND_DIR = REPO_ROOT / "src" / "api" / "backend"
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
def aws_region():
    """Provide the AWS region."""
    return "us-east-1"


@pytest.fixture(scope="session")
def lambda_client(request):
    """Create a Lambda client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("lambda", region_name=region)


@pytest.fixture(scope="session")
def s3_client(request):
    """Create an S3 client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("s3", region_name=region)


@pytest.fixture(scope="session")
def apigateway_client(request):
    """Create an API Gateway client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("apigateway", region_name=region)


@pytest.fixture(scope="session")
def ecs_runner_terraform_initialized():
    """Initialize terraform for ecs_runner state access."""
    return _terraform_init(ECS_RUNNER_DIR)


@pytest.fixture(scope="session")
def api_backend_terraform_initialized():
    """Initialize terraform for api_backend state access."""
    return _terraform_init(API_BACKEND_DIR)


@pytest.fixture(scope="session")
def www_shared_terraform_initialized():
    """Initialize terraform for www_shared state access."""
    return _terraform_init(WWW_SHARED_DIR)


@pytest.fixture(scope="session")
def ecs_runner_outputs(request):
    """Get ecs_runner terraform outputs."""
    if not request.getfixturevalue("ecs_runner_terraform_initialized"):
        pytest.skip("Terraform init failed for ecs_runner")
    return {
        "lambda_function_arn": _terraform_output(
            ECS_RUNNER_DIR, "lambda_function_arn"
        ),
        "lambda_function_name": _terraform_output(
            ECS_RUNNER_DIR, "lambda_function_name"
        ),
        "cluster_arn": _terraform_output(
            ECS_RUNNER_DIR, "cluster_arn"
        ),
        "cluster_name": _terraform_output(
            ECS_RUNNER_DIR, "cluster_name"
        ),
    }


@pytest.fixture(scope="session")
def api_backend_outputs(request):
    """Get api_backend terraform outputs."""
    if not request.getfixturevalue("api_backend_terraform_initialized"):
        pytest.skip("Terraform init failed for api_backend")
    return {
        "api_gateway_id": _terraform_output(
            API_BACKEND_DIR, "api_gateway_id"
        ),
        "api_gateway_execution_arn": _terraform_output(
            API_BACKEND_DIR, "api_gateway_execution_arn"
        ),
    }


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
    }
