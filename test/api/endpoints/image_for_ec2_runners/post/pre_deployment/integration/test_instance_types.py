"""Integration tests for EC2 instance type availability."""
from botocore.exceptions import ClientError


class TestInstanceTypesAvailability:
    """Tests for instance types availability."""

    def test_instance_types_are_valid(self, ec2_client, instance_types):
        """Instance types are valid."""

        all_valid = False
        if instance_types:
            try:
                response = ec2_client.describe_instance_types(InstanceTypes=instance_types)
                found_types = [t["InstanceType"] for t in response.get("InstanceTypes", [])]
                all_valid = all(t in found_types for t in instance_types)
            except ClientError:
                all_valid = False
        assert all_valid

    def test_instance_types_available_in_region(self, ec2_client, instance_types, aws_region):
        """Instance types available in region."""

        all_available = False
        if instance_types:
            try:
                response = ec2_client.describe_instance_type_offerings(
                    LocationType="region",
                    Filters=[
                        {"Name": "instance-type", "Values": instance_types},
                        {"Name": "location", "Values": [aws_region]},
                    ],
                )
                found_types = [o["InstanceType"] for o in response.get("InstanceTypeOfferings", [])]
                all_available = all(t in found_types for t in instance_types)
            except ClientError:
                all_available = False
        assert all_available

    def test_instance_types_have_instance_storage(self, ec2_client, instance_types):
        """Instance types have instance storage."""

        all_have_storage = False
        if instance_types:
            try:
                response = ec2_client.describe_instance_types(InstanceTypes=instance_types)
                types = response.get("InstanceTypes", [])
                if types:
                    all_have_storage = all(
                        t.get("InstanceStorageSupported", False) for t in types
                    )
            except ClientError:
                all_have_storage = False
        assert all_have_storage
