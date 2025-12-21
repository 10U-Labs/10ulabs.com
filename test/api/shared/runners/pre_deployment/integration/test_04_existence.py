"""Layer 4: Existence tests for api/shared/runners pre-deployment.

Tests that prerequisite resources exist. Assumes authorization passed.

Six-layer testing model:
- Layer 4: Existence - Resource actually exists
"""

from botocore.exceptions import ClientError
import pytest


pytestmark = pytest.mark.layer(4)


class TestPrerequisiteResourcesExist:
    """Layer 4: Verify prerequisite resources exist."""

    def test_iam_role_exists(self, iam_client, current_role_name):
        """Verify the IAM role exists."""
        if not current_role_name:
            pytest.skip("Could not determine current role name")
        try:
            response = iam_client.get_role(RoleName=current_role_name)
            assert response["Role"]["RoleName"] == current_role_name
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(
                    f"IAM role '{current_role_name}' does not exist. "
                    "Run terraform apply in src/bootstrap/"
                )
            raise

    def test_state_bucket_exists(self, s3_client, state_bucket_name):
        """Verify the terraform state bucket exists."""
        try:
            response = s3_client.head_bucket(Bucket=state_bucket_name)
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                pytest.fail(
                    f"Terraform state bucket '{state_bucket_name}' does not exist. "
                    "Run terraform apply in src/bootstrap/"
                )
            raise
