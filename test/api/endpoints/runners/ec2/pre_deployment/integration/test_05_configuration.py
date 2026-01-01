"""Layer 5: Configuration tests.

Verify prerequisite resources are configured correctly.
"""
import pytest

from .conftest import get_stable_ami_filters

pytestmark = pytest.mark.layer(5)


def test_stable_ami_is_available(ec2_client):
    """Verify the stable AMI is in available state."""
    response = ec2_client.describe_images(
        Owners=["self"],
        Filters=get_stable_ami_filters() + [{"Name": "state", "Values": ["available"]}]
    )
    has_available_ami = len(response["Images"]) >= 1
    assert has_available_ami, (
        "No stable AMI in 'available' state. Wait for AMI creation to complete."
    )


class TestVPCConfiguration:
    """Verify VPC resources are properly configured."""

    def test_vpc_is_available(self, ec2_client, networking_outputs):
        """Verify the VPC is in available state."""
        vpc_id = networking_outputs.get("vpc_id")
        if not vpc_id:
            pytest.skip("vpc_id output not found")
        response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
        if not response["Vpcs"]:
            pytest.skip("VPC not found")
        vpc = response["Vpcs"][0]
        assert vpc["State"] == "available", (
            f"VPC {vpc_id} is in state '{vpc['State']}', not 'available'."
        )

    def test_subnets_are_available(self, ec2_client, networking_outputs):
        """Verify all subnets are in available state."""
        subnet_ids_str = networking_outputs.get("public_subnets_ids")
        if not subnet_ids_str:
            pytest.skip("public_subnets_ids output not found")
        subnet_ids = [s.strip() for s in subnet_ids_str.split(",") if s.strip()]
        response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
        for subnet in response["Subnets"]:
            assert subnet["State"] == "available", (
                f"Subnet {subnet['SubnetId']} is in state '{subnet['State']}', "
                "not 'available'."
            )
