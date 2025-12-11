"""Pytest fixtures for pre-deployment integration tests."""
import subprocess
from pathlib import Path

import boto3
import pytest


REPO_ROOT = Path(__file__).resolve().parents[6]
EC2_RUNNER_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "ec2_runner"
ECS_RUNNER_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "ecs_runner"


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
def sqs_client(request):
    """Create an SQS client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("sqs", region_name=region)


@pytest.fixture(scope="session")
def dynamodb_client(request):
    """Create a DynamoDB client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("dynamodb", region_name=region)


@pytest.fixture(scope="session")
def ec2_runner_terraform_initialized():
    """Initialize terraform for ec2_runner state access."""
    return _terraform_init(EC2_RUNNER_DIR)


@pytest.fixture(scope="session")
def ecs_runner_terraform_initialized():
    """Initialize terraform for ecs_runner state access."""
    return _terraform_init(ECS_RUNNER_DIR)


@pytest.fixture(scope="session")
def ec2_runner_outputs(request):
    """Get ec2_runner terraform outputs."""
    if not request.getfixturevalue("ec2_runner_terraform_initialized"):
        pytest.skip("Terraform init failed for ec2_runner")
    return {
        "lambda_function_arn": _terraform_output(
            EC2_RUNNER_DIR, "lambda_function_arn"
        ),
        "lambda_function_name": _terraform_output(
            EC2_RUNNER_DIR, "lambda_function_name"
        ),
        "lambda_invoke_arn": _terraform_output(
            EC2_RUNNER_DIR, "lambda_invoke_arn"
        ),
        "ec2_instance_profile_name": _terraform_output(
            EC2_RUNNER_DIR, "ec2_instance_profile_name"
        ),
        "ec2_runner_role_arn": _terraform_output(
            EC2_RUNNER_DIR, "ec2_runner_role_arn"
        ),
    }


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
        "task_definition_arn": _terraform_output(
            ECS_RUNNER_DIR, "task_definition_arn"
        ),
    }
