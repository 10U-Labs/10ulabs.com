"""Layer 2: Authorization tests for api/shared/ecs_runner pre-deployment.

Tests that credentials have permission to INSPECT prerequisite resources.
Not existence, not capability - just permission to check.

Six-layer testing model:
- Layer 2: Authorization - Permission to inspect resources
"""

from botocore.exceptions import ClientError
import pytest


pytestmark = pytest.mark.layer(2)


class TestIAMRoleInspectionAuthorization:
    """Layer 2: Verify permission to inspect IAM roles."""

    def test_can_call_iam_get_role_api(self, iam_client, current_role_name):
        """Verify we have permission to call iam:GetRole."""
        if not current_role_name:
            pytest.skip("Could not determine current role name")
        try:
            iam_client.get_role(RoleName=current_role_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to call iam:GetRole on '{current_role_name}'. "
                    "The role may lack iam:GetRole permission for itself."
                )
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pass  # Role doesn't exist, but we have permission to check
            else:
                raise

    def test_can_list_attached_policies(self, iam_client, current_role_name):
        """Verify we have permission to call iam:ListAttachedRolePolicies."""
        if not current_role_name:
            pytest.skip("Could not determine current role name")
        try:
            iam_client.list_attached_role_policies(RoleName=current_role_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to call iam:ListAttachedRolePolicies "
                    f"on '{current_role_name}'."
                )
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pass  # Role doesn't exist, but we have permission to check
            else:
                raise


class TestS3BucketInspectionAuthorization:
    """Layer 2: Verify permission to inspect S3 buckets."""

    def test_can_call_s3_head_bucket_api(self, s3_client, state_bucket_name):
        """Verify we have permission to call s3:HeadBucket."""
        try:
            s3_client.head_bucket(Bucket=state_bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "403":
                pytest.fail(
                    f"No permission to call HeadBucket on '{state_bucket_name}'. "
                    "Check IAM permissions for s3:HeadBucket."
                )
            if e.response["Error"]["Code"] == "404":
                pass  # Bucket doesn't exist, but we have permission to check
            else:
                raise


class TestECRInspectionAuthorization:
    """Layer 2: Verify permission to inspect ECR repositories."""

    def test_can_call_ecr_describe_repositories_api(self, ecr_client):
        """Verify we have permission to call ecr:DescribeRepositories."""
        try:
            ecr_client.describe_repositories(maxResults=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call ecr:DescribeRepositories. "
                    "Check IAM permissions for ecr:DescribeRepositories."
                )
            raise
