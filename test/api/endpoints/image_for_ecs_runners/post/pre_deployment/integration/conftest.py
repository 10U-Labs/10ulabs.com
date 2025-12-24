"""Pytest fixtures for pre-deployment integration tests.

Common fixtures (terraform_init, terraform_output) are inherited from
test/api/conftest.py.
"""
from test.api.conftest import REPO_ROOT, terraform_init, terraform_output

import boto3
import pytest
import requests
from botocore.exceptions import ClientError

# Enable layer marker plugin for test ordering
pytest_plugins = ['pytest_layers']


API_SHARED_ECR_DIR = REPO_ROOT / "src" / "api" / "shared" / "ecs_runner"
AWS_REGION = "us-east-1"
BASE_IMAGE = "debian"
BASE_TAG = "stable-slim"


@pytest.fixture(scope="module")
def sts_client():
    """Create STS client for authentication tests."""
    return boto3.client("sts", region_name=AWS_REGION)


@pytest.fixture(scope="module")
def ecr_client():
    """Create ECR client for repository tests."""
    return boto3.client("ecr", region_name=AWS_REGION)


@pytest.fixture(scope="session")
def terraform_initialized():
    """Initialize terraform for api_shared_ecr state access."""
    return terraform_init(API_SHARED_ECR_DIR)


@pytest.fixture(scope="session")
def api_shared_ecr_outputs(request):
    """Get api_shared_ecr terraform outputs."""
    assert request.getfixturevalue("terraform_initialized"), (
        "Terraform init failed for api_shared_ecr"
    )
    return {
        "repository_name": terraform_output(API_SHARED_ECR_DIR, "ecr_repository_name"),
        "repository_url": terraform_output(API_SHARED_ECR_DIR, "ecr_repository_url"),
        "repository_arn": terraform_output(API_SHARED_ECR_DIR, "ecr_repository_arn"),
    }


@pytest.fixture(scope="module")
def ecr_repository_details(request):
    """Get ECR repository details, skipping if not available."""
    client = request.getfixturevalue("ecr_client")
    outputs = request.getfixturevalue("api_shared_ecr_outputs")
    repository_name = outputs.get("repository_name")
    if not repository_name:
        pytest.skip("repository_name output not available")
    try:
        response = client.describe_repositories(repositoryNames=[repository_name])
        if not response["repositories"]:
            pytest.skip("Repository does not exist")
        return response["repositories"][0]
    except ClientError as e:
        if e.response["Error"]["Code"] == "RepositoryNotFoundException":
            pytest.skip("Repository does not exist")
        raise


@pytest.fixture(scope="module")
def docker_hub_image_data():
    """Get Docker Hub image data for base image."""
    url = f"https://hub.docker.com/v2/repositories/library/{BASE_IMAGE}/tags/{BASE_TAG}"
    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        pytest.skip("Base image not found on Docker Hub")
    return response.json()
