"""Layer 7: Capability tests.

Verify we can perform required operations on prerequisite resources.
"""
from botocore.exceptions import ClientError
import pytest


class TestECRCapability:
    """Verify ECR operations can be performed."""

    def test_can_describe_ecr_images(self, ecr_client, ecr_repository_name):
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
        assert True  # Explicit pass

    def test_can_list_ecr_images(self, ecr_client, ecr_repository_name):
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
        assert True  # Explicit pass


class TestSSMCapability:
    """Verify SSM operations can be performed."""

    def test_can_get_github_token_parameter(self, ssm_client, github_token_parameter_name):
        """Verify we can read the GitHub token SSM parameter."""
        try:
            ssm_client.get_parameter(
                Name=github_token_parameter_name,
                WithDecryption=True
            )
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDeniedException":
                pytest.fail(
                    f"No permission to call ssm:GetParameter on '{github_token_parameter_name}'. "
                    "The Lambda role needs ssm:GetParameter permission."
                )
            if error_code == "ParameterNotFound":
                pytest.skip(
                    f"SSM parameter '{github_token_parameter_name}' does not exist. "
                    "Ensure the GitHub PAT is configured in SSM."
                )
            raise
        assert True  # Explicit pass
