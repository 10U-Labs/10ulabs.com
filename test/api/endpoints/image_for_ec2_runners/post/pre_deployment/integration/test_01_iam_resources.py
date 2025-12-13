"""Integration tests for IAM resources required for AMI building.

Five-layer testing model:
- Layer 3: Existence - Does the IAM instance profile exist?
- Layer 4: Configuration - Does the instance profile have a role attached?

These tests verify that IAM resources from bootstrap exist before AMI building.
"""

from botocore.exceptions import ClientError
import pytest


class TestIamInstanceProfile:
    """Layer 3-4: Verify IAM instance profile exists and is configured."""

    def test_instance_profile_exists(self, iam_client, config):
        """Verify runner instance profile exists."""
        profile_name = config.get("github_runner_iam_instance_profile_name", "")
        if not profile_name:
            pytest.skip("github_runner_iam_instance_profile_name not configured")
        try:
            response = iam_client.get_instance_profile(InstanceProfileName=profile_name)
            assert response.get("InstanceProfile") is not None, (
                f"Instance profile '{profile_name}' response missing InstanceProfile. "
                "Run terraform apply in src/bootstrap/"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(
                    f"Instance profile '{profile_name}' does not exist. "
                    "Run terraform apply in src/bootstrap/"
                )
            raise

    def test_instance_profile_has_role_attached(self, iam_client, config):
        """Verify runner instance profile has a role attached."""
        profile_name = config.get("github_runner_iam_instance_profile_name", "")
        if not profile_name:
            pytest.skip("github_runner_iam_instance_profile_name not configured")
        try:
            response = iam_client.get_instance_profile(InstanceProfileName=profile_name)
            profile = response.get("InstanceProfile", {})
            roles = profile.get("Roles", [])
            assert len(roles) > 0, (
                f"Instance profile '{profile_name}' has no roles attached. "
                "The profile must have an IAM role for EC2 instances to assume."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip("Instance profile does not exist")
            raise
