"""Integration tests for IAM resources required for AMI building."""
from botocore.exceptions import ClientError


class TestIamInstanceProfile:
    """Tests for iam instance profile."""

    def test_runner_instance_profile_exists(self, iam_client, config):
        """Runner instance profile exists."""

        exists = False
        profile_name = config.get("github_runner_iam_instance_profile_name", "")
        if profile_name:
            try:
                response = iam_client.get_instance_profile(InstanceProfileName=profile_name)
                exists = response.get("InstanceProfile") is not None
            except ClientError:
                exists = False
        assert exists

    def test_runner_instance_profile_has_role(self, iam_client, config):
        """Runner instance profile has role."""

        has_role = False
        profile_name = config.get("github_runner_iam_instance_profile_name", "")
        if profile_name:
            try:
                response = iam_client.get_instance_profile(InstanceProfileName=profile_name)
                profile = response.get("InstanceProfile", {})
                roles = profile.get("Roles", [])
                has_role = len(roles) > 0
            except ClientError:
                has_role = False
        assert has_role
