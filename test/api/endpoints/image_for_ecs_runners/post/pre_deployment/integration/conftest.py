"""Pytest fixtures for pre-deployment integration tests.

Common fixtures (terraform_init, terraform_output) are inherited from
test/api/conftest.py.
"""
from test.api.conftest import REPO_ROOT, terraform_init, terraform_output

import pytest


API_SHARED_ECR_DIR = REPO_ROOT / "src" / "api" / "shared" / "ecs_runner"


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
