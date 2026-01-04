"""Pytest fixtures for pre-deployment integration tests.

Common fixtures (terraform_init, terraform_output) are inherited from
test/api/conftest.py.
"""
from test.api.conftest import REPO_ROOT, terraform_init, terraform_output

import pytest
import requests

pytest_plugins = ['test_fixtures.aws']

API_COMMON_ECR_DIR = REPO_ROOT / "src" / "api" / "common" / "docker_repository"
BASE_IMAGE = "debian"
BASE_TAG = "stable-slim"


@pytest.fixture(scope="session")
def terraform_initialized():
    """Initialize terraform for api_common_ecr state access."""
    return terraform_init(API_COMMON_ECR_DIR)


@pytest.fixture(scope="session")
def api_common_ecr_outputs(request):
    """Get api_common_ecr terraform outputs."""
    assert request.getfixturevalue("terraform_initialized"), (
        "Terraform init failed for api_common_ecr"
    )
    return {
        "repository_name": terraform_output(API_COMMON_ECR_DIR, "ecr_repository_name"),
        "repository_url": terraform_output(API_COMMON_ECR_DIR, "ecr_repository_url"),
        "repository_arn": terraform_output(API_COMMON_ECR_DIR, "ecr_repository_arn"),
    }


@pytest.fixture(scope="module")
def ecr_repository_details(request):
    """Get ECR repository details."""
    client = request.getfixturevalue("ecr_client")
    outputs = request.getfixturevalue("api_common_ecr_outputs")
    repository_name = outputs.get("repository_name")
    assert repository_name, "repository_name output not available"
    response = client.describe_repositories(repositoryNames=[repository_name])
    assert response["repositories"], "Repository does not exist"
    return response["repositories"][0]


@pytest.fixture(scope="module")
def docker_hub_image_data():
    """Get Docker Hub image data for base image."""
    url = f"https://hub.docker.com/v2/repositories/library/{BASE_IMAGE}/tags/{BASE_TAG}"
    response = requests.get(url, timeout=30)
    assert response.status_code == 200, "Base image not found on Docker Hub"
    return response.json()
