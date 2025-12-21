"""Layer 5: Configuration tests for api/shared/ecs_runner pre-deployment.

Tests that prerequisite resources are configured correctly. Assumes existence passed.

Six-layer testing model:
- Layer 5: Configuration - Resource configured correctly
"""

from botocore.exceptions import ClientError
import pytest


pytestmark = pytest.mark.layer(5)


class TestPrerequisiteResourcesConfiguration:
    """Layer 5: Verify prerequisite resources are configured correctly."""

    def test_role_has_administrator_access_policy(
        self, iam_client, current_role_name
    ):
        """Verify the role has AdministratorAccess policy attached."""
        if not current_role_name:
            pytest.skip("Could not determine current role name")
        try:
            response = iam_client.list_attached_role_policies(
                RoleName=current_role_name
            )
            policy_names = [p["PolicyName"] for p in response["AttachedPolicies"]]
            assert "AdministratorAccess" in policy_names, (
                f"Role '{current_role_name}' missing AdministratorAccess policy. "
                f"Attached policies: {policy_names}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.skip(
                    "Cannot verify - no permission to list attached policies"
                )
            raise

    def test_bucket_has_encryption_enabled(self, s3_client, state_bucket_name):
        """Verify bucket encryption is enabled."""
        try:
            response = s3_client.get_bucket_encryption(Bucket=state_bucket_name)
            rules = response.get(
                "ServerSideEncryptionConfiguration", {}
            ).get("Rules", [])
            assert len(rules) > 0, (
                f"Bucket '{state_bucket_name}' has no encryption rules configured. "
                "Terraform state buckets should have server-side encryption enabled."
            )
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "ServerSideEncryptionConfigurationNotFoundError":
                pytest.fail(
                    f"Bucket '{state_bucket_name}' has no encryption configured. "
                    "Terraform state buckets should have server-side encryption."
                )
            raise

    def test_bucket_in_expected_region(
        self, s3_client, state_bucket_name, state_bucket_region
    ):
        """Verify bucket is in the expected region."""
        response = s3_client.get_bucket_location(Bucket=state_bucket_name)
        # AWS returns None for us-east-1, otherwise the region name
        location = response.get("LocationConstraint")
        actual_region = location if location else "us-east-1"
        assert actual_region == state_bucket_region, (
            f"Bucket '{state_bucket_name}' is in region '{actual_region}', "
            f"expected '{state_bucket_region}'."
        )
