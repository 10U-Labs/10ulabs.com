"""Layer 5: Configuration tests.

Verify prerequisite resources are configured correctly.
"""
from botocore.exceptions import ClientError
import pytest

pytestmark = pytest.mark.layer(5)


@pytest.fixture(name="ecr_repo", scope="module")
def ecr_repo_fixture(ecr_client, ecr_repository_name):
    """Get ECR repository details."""
    if not ecr_repository_name:
        pytest.fail("ECR repository name not configured")
        return None
    try:
        response = ecr_client.describe_repositories(
            repositoryNames=[ecr_repository_name]
        )
        return response["repositories"][0]
    except ClientError as e:
        if e.response["Error"]["Code"] == "RepositoryNotFoundException":
            pytest.skip(f"ECR repository '{ecr_repository_name}' does not exist")
        raise


def test_ecr_repository_has_uri(ecr_repo):
    """Verify the ECR repository has repositoryUri field."""
    assert "repositoryUri" in ecr_repo


def test_ecr_repository_uri_not_empty(ecr_repo):
    """Verify the ECR repository URI is not empty."""
    assert ecr_repo["repositoryUri"]


def test_ecr_repository_uri_contains_ecr(ecr_repo):
    """Verify the ECR repository URI contains .ecr."""
    assert ".ecr." in ecr_repo["repositoryUri"]


def test_ecr_repository_uri_contains_amazonaws(ecr_repo):
    """Verify the ECR repository URI contains .amazonaws.com."""
    assert ".amazonaws.com/" in ecr_repo["repositoryUri"]
