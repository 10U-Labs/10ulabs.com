"""Fixtures for runners/ecs/images endpoint pre-deployment integration tests."""
from test.api.endpoints.runners.ecs.images.conftest import get_ecr_repository

from botocore.exceptions import ClientError
import pytest

# Enable layer marker plugin for test ordering
pytest_plugins = ['pytest_layers']


@pytest.fixture(scope="session")
def ecr_repository_name():
    """Provide the ECR repository name."""
    return get_ecr_repository()


@pytest.fixture(name="ecr_repo", scope="module")
def ecr_repo_fixture(ecr_client, request):
    """Get ECR repository details."""
    repo_name = request.getfixturevalue("ecr_repository_name")
    if not repo_name:
        pytest.fail("ECR repository name not configured")
        return None
    try:
        response = ecr_client.describe_repositories(
            repositoryNames=[repo_name]
        )
        return response["repositories"][0]
    except ClientError as e:
        if e.response["Error"]["Code"] == "RepositoryNotFoundException":
            pytest.fail(
                f"ECR repository '{repo_name}' does not exist. "
                "Run terraform apply in src/api/shared/ecs_runner/"
            )
        raise
