"""Layer 3: Existence tests.

These tests verify that prerequisite resources exist. Assumes authorization
(Layer 2) has passed.
"""
import pytest
from botocore.exceptions import ClientError


class TestIamResourcesExist:
    """Tests for IAM resources existence."""

    def test_iam_instance_profile_exists(
        self, fetched_instance_profile, instance_profile_name
    ):
        """Verify runner instance profile exists."""
        if not instance_profile_name:
            pytest.skip("github_runner_iam_instance_profile_name not configured")

        assert fetched_instance_profile is not None, (
            f"Instance profile '{instance_profile_name}' does not exist. "
            "Run terraform apply in src/bootstrap/"
        )

    def test_iam_instance_profile_has_arn(
        self, fetched_instance_profile, instance_profile_name
    ):
        """Verify runner instance profile has an ARN."""
        if not instance_profile_name:
            pytest.skip("github_runner_iam_instance_profile_name not configured")

        if fetched_instance_profile is None:
            pytest.skip("Instance profile does not exist")

        assert fetched_instance_profile.get("Arn", "").startswith("arn:aws:iam::")


class TestTerraformOutputsExist:
    """Tests for Terraform outputs existence."""

    def test_terraform_init_succeeds(self, terraform_initialized):
        """Verify Terraform init succeeds."""
        assert terraform_initialized

    def test_ec2_runner_ami_purpose_value_exists(self, terraform_outputs):
        """Verify ec2_runner_ami_purpose_value output exists."""
        assert terraform_outputs.get("ec2_runner_ami_purpose_value") != ""

    def test_ec2_runner_ami_stable_tag_exists(self, terraform_outputs):
        """Verify ec2_runner_ami_stable_tag output exists."""
        assert terraform_outputs.get("ec2_runner_ami_stable_tag") != ""

    def test_security_group_id_for_runners_exists(self, terraform_outputs):
        """Verify security_group_id_for_runners output exists."""
        assert terraform_outputs.get("security_group_id_for_runners") != ""

    def test_public_subnets_ids_exists(self, terraform_outputs):
        """Verify public_subnets_ids output exists."""
        assert terraform_outputs.get("public_subnets_ids") != ""

    def test_ec2_instance_types_exists(self, terraform_outputs):
        """Verify ec2_instance_types output exists."""
        assert terraform_outputs.get("ec2_instance_types") != ""


class TestSecurityGroupExists:
    """Tests for security group existence."""

    def test_security_group_exists_in_aws(self, ec2_client, security_group_id):
        """Verify security group exists in AWS."""
        if not security_group_id:
            pytest.skip("No security group ID configured")

        try:
            response = ec2_client.describe_security_groups(GroupIds=[security_group_id])
            assert len(response.get("SecurityGroups", [])) > 0
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidGroup.NotFound":
                pytest.fail(f"Security group '{security_group_id}' does not exist")
            raise

    def test_security_group_returns_group_id(self, ec2_client, security_group_id):
        """Verify security group returns its group ID."""
        if not security_group_id:
            pytest.skip("No security group ID configured")

        try:
            response = ec2_client.describe_security_groups(GroupIds=[security_group_id])
            sg = response.get("SecurityGroups", [{}])[0]
            assert sg.get("GroupId") == security_group_id
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidGroup.NotFound":
                pytest.skip("Security group does not exist")
            raise


class TestSubnetsExist:
    """Tests for subnets existence."""

    def test_all_subnets_exist_in_aws(self, ec2_client, subnet_ids):
        """Verify all configured subnets exist in AWS."""
        if not subnet_ids:
            pytest.skip("No subnet IDs configured")

        try:
            response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
            found_count = len(response.get("Subnets", []))
            assert found_count == len(subnet_ids)
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidSubnetID.NotFound":
                pytest.fail(f"One or more subnets do not exist: {subnet_ids}")
            raise

    def test_subnets_return_subnet_ids(self, ec2_client, subnet_ids):
        """Verify subnets return their IDs."""
        if not subnet_ids:
            pytest.skip("No subnet IDs configured")

        try:
            response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
            found_ids = [s["SubnetId"] for s in response.get("Subnets", [])]
            assert set(found_ids) == set(subnet_ids)
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidSubnetID.NotFound":
                pytest.skip("One or more subnets do not exist")
            raise


class TestSourceAmiExists:
    """Tests for source AMI existence."""

    def test_source_ami_exists_in_aws(
        self, source_ami_images, source_ami_pattern_configured
    ):
        """Verify source AMI exists in AWS."""
        if not source_ami_pattern_configured:
            pytest.skip("Source AMI pattern not configured")

        assert len(source_ami_images) > 0

    def test_source_ami_has_image_id(
        self, source_ami_images, source_ami_pattern_configured
    ):
        """Verify source AMI has an image ID."""
        if not source_ami_pattern_configured:
            pytest.skip("Source AMI pattern not configured")

        if not source_ami_images:
            pytest.skip("No matching AMI found")

        assert source_ami_images[0].get("ImageId", "").startswith("ami-")
