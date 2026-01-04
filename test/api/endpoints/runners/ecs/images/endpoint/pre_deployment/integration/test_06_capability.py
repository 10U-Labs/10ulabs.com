"""Layer 6: Capability tests.

Verify we can perform required operations on prerequisite resources.
"""
from botocore.exceptions import ClientError
import pytest



def test_can_describe_ecr_images(ecr_client, ecr_repository_name):
    """Verify we can describe images in the repository."""
    try:
        ecr_client.describe_images(
            repositoryName=ecr_repository_name,
            maxResults=1
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDeniedException":
            pytest.fail(
                f"No permission to call ecr:DescribeImages on '{ecr_repository_name}'. "
                "The Lambda role needs ecr:DescribeImages permission."
            )
        if e.response["Error"]["Code"] == "RepositoryNotFoundException":
            pytest.skip(f"ECR repository '{ecr_repository_name}' does not exist")
        raise


def test_can_list_ecr_images(ecr_client, ecr_repository_name):
    """Verify we can list images in the repository."""
    try:
        ecr_client.list_images(
            repositoryName=ecr_repository_name,
            maxResults=1
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDeniedException":
            pytest.fail(
                f"No permission to call ecr:ListImages on '{ecr_repository_name}'. "
                "The Lambda role needs ecr:ListImages permission."
            )
        if e.response["Error"]["Code"] == "RepositoryNotFoundException":
            pytest.skip(f"ECR repository '{ecr_repository_name}' does not exist")
        raise
