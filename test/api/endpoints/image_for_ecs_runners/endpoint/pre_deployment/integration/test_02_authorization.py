"""Layer 2: Authorization tests.

Verify we have permission to inspect prerequisite resources.
"""
from botocore.exceptions import ClientError
import pytest

pytestmark = pytest.mark.layer(2)


def test_can_describe_ecr_repositories(ecr_client, ecr_repository_name):
    """Verify permission to call ecr:DescribeRepositories."""
    if not ecr_repository_name:
        pytest.fail("ECR repository name not configured")
    try:
        ecr_client.describe_repositories(repositoryNames=[ecr_repository_name])
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDeniedException":
            pytest.fail(
                f"No permission to call ecr:DescribeRepositories on "
                f"'{ecr_repository_name}'. Check IAM policy."
            )
        if e.response["Error"]["Code"] == "RepositoryNotFoundException":
            pass  # Repository doesn't exist, but we have permission - OK for layer 2
        else:
            raise


def test_can_list_ecr_images(ecr_client, ecr_repository_name):
    """Verify permission to call ecr:ListImages."""
    if not ecr_repository_name:
        pytest.skip("ECR repository name not configured")
    try:
        ecr_client.list_images(repositoryName=ecr_repository_name, maxResults=1)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDeniedException":
            pytest.fail(
                f"No permission to call ecr:ListImages on '{ecr_repository_name}'. "
                "Check IAM policy."
            )
        if e.response["Error"]["Code"] == "RepositoryNotFoundException":
            pass  # Repository doesn't exist, but we have permission - OK for layer 2
        else:
            raise
