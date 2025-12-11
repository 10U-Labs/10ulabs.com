"""Pytest fixtures for pre-deployment integration tests."""
import importlib
import subprocess
import sys
from pathlib import Path

import boto3
import pytest


REPO_ROOT = Path(__file__).resolve().parents[6]
EC2_RUNNER_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "ec2_runner"
ECS_RUNNER_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "ecs_runner"

# Add lib/python to path for terraform_config module
LIB_DIR = REPO_ROOT / "lib" / "python"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))


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


def _get_shared_config():
    """Load shared config from terraform_config module."""
    terraform_config = importlib.import_module("terraform_config")
    return terraform_config.get_shared_config()


@pytest.fixture(scope="session")
def shared_config():
    """Provide shared config from terraform module."""
    return _get_shared_config()


@pytest.fixture(scope="session")
def aws_region(request):
    """Provide the AWS region from shared config."""
    cfg = request.getfixturevalue("shared_config")
    return cfg.get("aws_region", "us-east-2")


@pytest.fixture(scope="session")
def config(request):
    """Provide config for integration tests."""
    cfg = request.getfixturevalue("shared_config")
    return {
        'resource_prefix': cfg.get('resource_prefix', 'TenULabs'),
        'aws_region': cfg.get('aws_region', 'us-east-2'),
    }


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
