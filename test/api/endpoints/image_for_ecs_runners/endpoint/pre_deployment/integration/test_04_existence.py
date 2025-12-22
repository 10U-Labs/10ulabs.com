"""Layer 4: Existence tests.

Verify prerequisite resources exist.
"""
from botocore.exceptions import ClientError
import pytest

pytestmark = pytest.mark.layer(4)


@pytest.fixture(name="ecr_repo", scope="module")
def ecr_repo_fixture(ecr_client, ecr_repository_name):
    """Get ECR repository details."""
    if not ecr_repository_name:
        pytest.fail("ECR repository name not configured")
        return None  # Unreachable but satisfies pylint
    try:
        response = ecr_client.describe_repositories(
            repositoryNames=[ecr_repository_name]
        )
        return response["repositories"][0]
    except ClientError as e:
        if e.response["Error"]["Code"] == "RepositoryNotFoundException":
            pytest.fail(
                f"ECR repository '{ecr_repository_name}' does not exist. "
                "Run terraform apply in src/api/shared/ecs_runner/"
            )
        raise


def test_ecr_repository_exists(ecr_repo, ecr_repository_name):
    """Verify the ECR repository exists."""
    assert ecr_repo["repositoryName"] == ecr_repository_name


def test_ecr_repository_has_arn(ecr_repo):
    """Verify the ECR repository has ARN."""
    assert "repositoryArn" in ecr_repo


def test_ecr_repository_arn_contains_ecr(ecr_repo):
    """Verify the ECR repository ARN contains :ecr:."""
    assert ":ecr:" in ecr_repo["repositoryArn"]
