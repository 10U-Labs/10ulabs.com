"""Layer 2: Authorization tests for ECS runner image deployment.

These tests verify that credentials have permission to inspect prerequisite resources.
Per PRE_DEPLOYMENT_INTEGRATION_TESTS.md tenets, authorization tests verify
permission to inspect - not existence or capability.
"""
from botocore.exceptions import ClientError

import pytest

pytestmark = pytest.mark.layer(2)


class TestECRAuthorization:
    """Verify permission to inspect ECR repository."""

    def test_can_describe_ecr_repositories(self, ecr_client, api_shared_ecr_outputs):
        """Verify permission to call ecr:DescribeRepositories."""
        repository_name = api_shared_ecr_outputs.get("repository_name")
        if not repository_name:
            pytest.skip("repository_name output not available")
        try:
            ecr_client.describe_repositories(repositoryNames=[repository_name])
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    f"No permission to call ecr:DescribeRepositories on '{repository_name}'. "
                    "Check IAM policy."
                )
            if e.response["Error"]["Code"] == "RepositoryNotFoundException":
                pass  # Repository doesn't exist, but we have permission to check
            else:
                raise

    def test_can_get_authorization_token(self, ecr_client):
        """Verify permission to call ecr:GetAuthorizationToken."""
        try:
            ecr_client.get_authorization_token()
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call ecr:GetAuthorizationToken. "
                    "This is required to push Docker images to ECR."
                )
            raise
