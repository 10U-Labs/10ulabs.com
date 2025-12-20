"""Layer 3: Existence tests.

These tests verify that prerequisite resources exist. Assumes authorization
(Layer 2) has passed.
"""
import pytest
from botocore.exceptions import ClientError


class TestIamResourcesExist:
    """Tests for IAM resources existence."""

    def test_iam_instance_profile_exists(self, iam_client, config):
        """Verify runner instance profile exists."""
        profile_name = config.get("github_runner_iam_instance_profile_name", "")
        if not profile_name:
            pytest.skip("github_runner_iam_instance_profile_name not configured")

        try:
            response = iam_client.get_instance_profile(InstanceProfileName=profile_name)
            assert response.get("InstanceProfile") is not None
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(
                    f"Instance profile '{profile_name}' does not exist. "
                    "Run terraform apply in src/bootstrap/"
                )
            raise


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

    def test_runner_security_group_id_exists(self, terraform_outputs):
        """Verify runner_security_group_id output exists."""
        assert terraform_outputs.get("runner_security_group_id") != ""

    def test_ssm_parameter_name_for_latest_ami_exists(self, terraform_outputs):
        """Verify ssm_parameter_name_for_latest_ami output exists."""
        assert terraform_outputs.get("ssm_parameter_name_for_latest_ami") != ""

    def test_vpc_public_subnet_ids_exists(self, terraform_outputs):
        """Verify vpc_public_subnet_ids output exists."""
        assert terraform_outputs.get("vpc_public_subnet_ids") != ""

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


class TestSourceAmiExists:
    """Tests for source AMI existence."""

    def test_source_ami_exists_in_aws(self, ec2_client, source_ami_pattern):
        """Verify source AMI exists in AWS."""
        os_family = source_ami_pattern.get("os_family", "")
        os_version = source_ami_pattern.get("os_version", "")
        os_arch = source_ami_pattern.get("os_architecture", "arm64")

        if not os_family or not os_version:
            pytest.skip("Source AMI pattern not configured")

        arch_filter = "arm64" if os_arch == "arm64" else "x86_64"
        response = ec2_client.describe_images(
            Filters=[
                {"Name": "name", "Values": [f"{os_family}-{os_version}-*"]},
                {"Name": "architecture", "Values": [arch_filter]},
                {"Name": "state", "Values": ["available"]},
            ],
            Owners=["amazon", "self", "aws-marketplace"],
        )

        assert len(response.get("Images", [])) > 0, (
            f"No AMI found matching pattern: {os_family}-{os_version}-* ({arch_filter})"
        )
