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


IMAGE_FOR_ECS_RUNNERS_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "image_for_ecs_runners"
API_SHARED_ECR_DIR = REPO_ROOT / "src" / "api" / "shared" / "ecs_runner"
RUNNERS_DIR = REPO_ROOT / "src" / "api" / "shared" / "runners"


@pytest.fixture(scope="session")
def ec2_client(shared_config):
    """Create an EC2 client."""
    return boto3.client("ec2", region_name=shared_config["aws_region"])


@pytest.fixture(scope="session")
def image_for_ecs_runners_terraform_initialized():
    """Initialize terraform for image_for_ecs_runners state access."""
    return terraform_init(IMAGE_FOR_ECS_RUNNERS_DIR)


@pytest.fixture(scope="session")
def api_shared_ecr_terraform_initialized():
    """Initialize terraform for api_shared_ecr state access."""
    return terraform_init(API_SHARED_ECR_DIR)


@pytest.fixture(scope="session")
def runners_terraform_initialized():
    """Initialize terraform for runners state access."""
    return terraform_init(RUNNERS_DIR)


@pytest.fixture(scope="session")
def image_for_ecs_runners_outputs(request):
    """Get image_for_ecs_runners terraform outputs."""
    if not request.getfixturevalue("image_for_ecs_runners_terraform_initialized"):
        pytest.skip("Terraform init failed for image_for_ecs_runners")
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
def api_shared_ecr_outputs(request):
    """Get api_shared_ecr terraform outputs."""
    if not request.getfixturevalue("api_shared_ecr_terraform_initialized"):
        pytest.skip("Terraform init failed for api_shared_ecr")
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
