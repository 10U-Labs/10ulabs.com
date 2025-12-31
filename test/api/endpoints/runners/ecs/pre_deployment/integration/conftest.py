"""Pytest fixtures for pre-deployment integration tests.

Common fixtures (terraform_init, terraform_output) are inherited from
test/api/conftest.py.
"""
from test.api.conftest import (
    REPO_ROOT,
    get_runners_outputs,
    terraform_init,
    terraform_output,
)

import boto3
import pytest

# Enable layer marker plugin for test ordering
pytest_plugins = ['pytest_layers']


@pytest.fixture(scope="session")
def shared_config():
    """Provide shared configuration values."""
    return {"aws_region": "us-east-2"}


AWS_REGION = "us-east-2"


def get_repository_name_or_skip(ecr_outputs):
    """Get repository name from outputs or skip the test if not available."""
    repository_name = ecr_outputs.get("repository_name")
    if not repository_name:
        pytest.skip("repository_name output not available")
    return repository_name


@pytest.fixture(scope="session")
def sts_client():
    """Create an STS client for authentication tests."""
    return boto3.client("sts", region_name=AWS_REGION)


@pytest.fixture(scope="session")
def ecr_client():
    """Create an ECR client."""
    return boto3.client("ecr", region_name=AWS_REGION)


IMAGE_FOR_ECS_RUNNERS_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "ecs" / "images"
API_SHARED_ECR_DIR = REPO_ROOT / "src" / "api" / "shared" / "docker_repository"
RUNNERS_DIR = REPO_ROOT / "src" / "api" / "shared" / "networking"


@pytest.fixture(scope="session")
def ec2_client():
    """Create an EC2 client."""
    return boto3.client("ec2", region_name=AWS_REGION)


@pytest.fixture(scope="session")
def ecs_client():
    """Create an ECS client."""
    return boto3.client("ecs", region_name=AWS_REGION)


@pytest.fixture(scope="session")
def logs_client():
    """Create a CloudWatch Logs client."""
    return boto3.client("logs", region_name=AWS_REGION)


@pytest.fixture(scope="session")
def ecs_images_terraform_initialized():
    """Initialize terraform for ecs_images state access."""
    return terraform_init(IMAGE_FOR_ECS_RUNNERS_DIR)


@pytest.fixture(scope="session")
def api_common_ecr_terraform_initialized():
    """Initialize terraform for api_common_ecr state access."""
    return terraform_init(API_SHARED_ECR_DIR)


@pytest.fixture(scope="session")
def runners_terraform_initialized():
    """Initialize terraform for runners state access."""
    return terraform_init(RUNNERS_DIR)


@pytest.fixture(scope="session")
def ecs_images_outputs(request):
    """Get ecs_images terraform outputs."""
    if not request.getfixturevalue("ecs_images_terraform_initialized"):
        pytest.skip("Terraform init failed for ecs_images")
    return {
        "lambda_function_arn": terraform_output(
            IMAGE_FOR_ECS_RUNNERS_DIR, "lambda_function_arn"
        ),
        "lambda_function_name": terraform_output(
            IMAGE_FOR_ECS_RUNNERS_DIR, "lambda_function_name"
        ),
        "lambda_invoke_arn": terraform_output(
            IMAGE_FOR_ECS_RUNNERS_DIR, "lambda_invoke_arn"
        ),
    }


@pytest.fixture(scope="session")
def api_common_ecr_outputs(request):
    """Get api_common_ecr terraform outputs."""
    if not request.getfixturevalue("api_common_ecr_terraform_initialized"):
        pytest.skip("Terraform init failed for api_common_ecr")
    return {
        "repository_name": terraform_output(
            API_SHARED_ECR_DIR, "ecr_repository_name"
        ),
        "repository_url": terraform_output(
            API_SHARED_ECR_DIR, "ecr_repository_url"
        ),
        "repository_arn": terraform_output(
            API_SHARED_ECR_DIR, "ecr_repository_arn"
        ),
    }


@pytest.fixture(scope="session")
def runners_outputs(request):
    """Get runners terraform outputs for ECS runner tests."""
    if not request.getfixturevalue("runners_terraform_initialized"):
        pytest.skip("Terraform init failed for runners")
    return get_runners_outputs(RUNNERS_DIR)
