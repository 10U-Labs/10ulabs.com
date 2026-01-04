"""Layer 2: Authorization tests.

Verify we have permission to inspect prerequisite resources.
"""
from botocore.exceptions import ClientError
import pytest
from test_fixtures.integration import handle_ecr_authorization_error



def test_can_describe_ecr_repositories(ecr_client, ecr_repository_name):
    """Verify permission to call ecr:DescribeRepositories."""
    if not ecr_repository_name:
        pytest.fail("ECR repository name not configured")
    try:
        ecr_client.describe_repositories(repositoryNames=[ecr_repository_name])
    except ClientError as e:
        handle_ecr_authorization_error(
            e, "ecr:DescribeRepositories", ecr_repository_name
        )


def test_can_list_ecr_images(ecr_client, ecr_repository_name):
    """Verify permission to call ecr:ListImages."""
    if not ecr_repository_name:
        pytest.skip("ECR repository name not configured")
    try:
        ecr_client.list_images(repositoryName=ecr_repository_name, maxResults=1)
    except ClientError as e:
        handle_ecr_authorization_error(e, "ecr:ListImages", ecr_repository_name)
