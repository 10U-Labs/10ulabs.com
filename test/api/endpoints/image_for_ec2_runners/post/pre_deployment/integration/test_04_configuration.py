"""Layer 4: Configuration tests.

These tests verify that prerequisite resources are configured correctly.
Assumes existence (Layer 3) has passed.
"""
import pytest
from botocore.exceptions import ClientError


class TestIamResourcesConfiguration:
    """Tests for IAM resources configuration."""

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


class TestTerraformOutputFormats:
    """Tests for Terraform output formats."""

    def test_security_group_id_format(self, security_group_id):
        """Verify security group ID has correct format."""
        if not security_group_id:
            pytest.skip("No security group ID configured")

        assert security_group_id.startswith("sg-"), (
            f"Invalid security group ID format: {security_group_id}"
        )

    def test_subnet_ids_not_empty(self, subnet_ids):
        """Verify subnet IDs list is not empty."""
        assert len(subnet_ids) > 0, "No subnet IDs configured"

    def test_subnet_ids_format(self, subnet_ids):
        """Verify all subnet IDs have correct format."""
        if not subnet_ids:
            pytest.skip("No subnet IDs configured")

        for subnet_id in subnet_ids:
            assert subnet_id.startswith("subnet-"), (
                f"Invalid subnet ID format: {subnet_id}"
            )

    def test_instance_types_not_empty(self, instance_types):
        """Verify instance types list is not empty."""
        assert len(instance_types) > 0, "No instance types configured"


class TestSecurityGroupConfiguration:
    """Tests for security group configuration."""

    def test_security_group_has_description(self, ec2_client, security_group_id):
        """Verify security group has a description."""
        if not security_group_id:
            pytest.skip("No security group ID configured")

        response = ec2_client.describe_security_groups(GroupIds=[security_group_id])
        sg = response["SecurityGroups"][0]

        assert sg.get("Description", "") != "", (
            f"Security group '{security_group_id}' has no description"
        )

    def test_security_group_has_vpc_id(self, ec2_client, security_group_id):
        """Verify security group is associated with a VPC."""
        if not security_group_id:
            pytest.skip("No security group ID configured")

        response = ec2_client.describe_security_groups(GroupIds=[security_group_id])
        sg = response["SecurityGroups"][0]

        assert sg.get("VpcId", "") != "", (
            f"Security group '{security_group_id}' is not associated with a VPC"
        )


class TestSubnetsConfiguration:
    """Tests for subnets configuration."""

    def test_subnets_are_available(self, ec2_client, subnet_ids):
        """Verify all subnets are in available state."""
        if not subnet_ids:
            pytest.skip("No subnet IDs configured")

        response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
        subnets = response.get("Subnets", [])

        for subnet in subnets:
            assert subnet.get("State") == "available", (
                f"Subnet {subnet['SubnetId']} is not available: {subnet.get('State')}"
            )

    def test_subnets_have_available_ips(self, ec2_client, subnet_ids):
        """Verify all subnets have available IP addresses."""
        if not subnet_ids:
            pytest.skip("No subnet IDs configured")

        response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
        subnets = response.get("Subnets", [])

        for subnet in subnets:
            assert subnet.get("AvailableIpAddressCount", 0) > 0, (
                f"Subnet {subnet['SubnetId']} has no available IP addresses"
            )

    def test_subnets_are_public(self, ec2_client, subnet_ids):
        """Verify all subnets are public (auto-assign public IP)."""
        if not subnet_ids:
            pytest.skip("No subnet IDs configured")

        response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
        subnets = response.get("Subnets", [])

        for subnet in subnets:
            assert subnet.get("MapPublicIpOnLaunch", False), (
                f"Subnet {subnet['SubnetId']} is not configured for public IP assignment"
            )


class TestSourceAmiConfiguration:
    """Tests for source AMI configuration."""

    def test_source_ami_is_available(self, ec2_client, source_ami_pattern):
        """Verify source AMI is in available state."""
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

        images = response.get("Images", [])
        if not images:
            pytest.skip("No matching AMI found")

        assert images[0].get("State") == "available", (
            f"Source AMI is not available: {images[0].get('State')}"
        )


class TestInstanceTypesConfiguration:
    """Tests for instance types configuration."""

    def test_instance_types_are_valid(self, ec2_client, instance_types):
        """Verify all instance types are valid AWS instance types."""
        if not instance_types:
            pytest.skip("No instance types configured")

        response = ec2_client.describe_instance_types(InstanceTypes=instance_types)
        found_types = [t["InstanceType"] for t in response.get("InstanceTypes", [])]

        for instance_type in instance_types:
            assert instance_type in found_types, (
                f"Invalid instance type: {instance_type}"
            )

    def test_instance_types_available_in_region(
        self, ec2_client, instance_types, aws_region
    ):
        """Verify all instance types are available in the configured region."""
        if not instance_types:
            pytest.skip("No instance types configured")

        response = ec2_client.describe_instance_type_offerings(
            LocationType="region",
            Filters=[
                {"Name": "instance-type", "Values": instance_types},
                {"Name": "location", "Values": [aws_region]},
            ],
        )
        found_types = [
            o["InstanceType"] for o in response.get("InstanceTypeOfferings", [])
        ]

        for instance_type in instance_types:
            assert instance_type in found_types, (
                f"Instance type {instance_type} not available in {aws_region}"
            )

    def test_instance_types_have_instance_storage(self, ec2_client, instance_types):
        """Verify all instance types have instance storage."""
        if not instance_types:
            pytest.skip("No instance types configured")

        response = ec2_client.describe_instance_types(InstanceTypes=instance_types)
        types_info = response.get("InstanceTypes", [])

        for type_info in types_info:
            assert type_info.get("InstanceStorageSupported", False), (
                f"Instance type {type_info['InstanceType']} does not support "
                "instance storage"
            )
