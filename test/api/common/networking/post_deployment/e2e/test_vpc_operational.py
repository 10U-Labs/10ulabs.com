"""E2E tests for api/common/networking VPC operational status.

These tests verify the networking infrastructure is operational as a complete
system. For networking, this means the VPC and its components are in a usable
state for launching resources.
"""


class TestVPCOperational:
    """E2E: Verify VPC is operational for launching resources."""

    def test_vpc_state_is_available(self, runners_vpc):
        """Verify VPC is in available state."""
        assert runners_vpc["State"] == "available"

    def test_subnets_state_is_available(self, ec2_client):
        """Verify all runner subnets are in available state."""
        response = ec2_client.describe_subnets(
            Filters=[
                {"Name": "tag:Purpose", "Values": ["runners"]},
                {"Name": "tag:ManagedBy", "Values": ["terraform"]},
            ]
        )
        for subnet in response["Subnets"]:
            assert subnet["State"] == "available"

    def test_internet_gateway_is_attached(self, ec2_client, runners_vpc_id):
        """Verify internet gateway is attached (not detached)."""
        response = ec2_client.describe_internet_gateways(
            Filters=[{"Name": "attachment.vpc-id", "Values": [runners_vpc_id]}]
        )
        igw = response["InternetGateways"][0]
        attachments = igw.get("Attachments", [])
        assert len(attachments) == 1
        assert attachments[0]["State"] == "available"
