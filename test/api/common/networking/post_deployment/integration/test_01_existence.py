"""Layer 1: Existence tests for api/common/networking post-deployment.

Tests ONLY that resources exist. No configuration checks.
These tests verify that resources created by THIS workflow exist after deployment.

Three-layer testing model:
- Layer 1: Existence - Resources were created
"""

import pytest


pytestmark = pytest.mark.layer(1)


class TestVPCResourcesExist:
    """Layer 1: Verify VPC and networking resources exist."""

    def test_runners_vpc_exists(self, runners_vpc):
        """Verify the runners VPC exists."""
        assert runners_vpc is not None, (
            "Runners VPC not found. Run terraform apply in src/api/common/networking/"
        )

    def test_runners_subnets_exist(self, ec2_client):
        """Verify the runners subnets exist."""
        response = ec2_client.describe_subnets(
            Filters=[
                {"Name": "tag:Purpose", "Values": ["runners"]},
                {"Name": "tag:ManagedBy", "Values": ["terraform"]},
            ]
        )
        assert len(response["Subnets"]) >= 1, (
            "Runners subnets not found. "
            "Run terraform apply in src/api/common/networking/"
        )

    def test_runners_internet_gateway_exists(self, ec2_client):
        """Verify the runners internet gateway exists."""
        response = ec2_client.describe_internet_gateways(
            Filters=[
                {"Name": "tag:Purpose", "Values": ["runners"]},
                {"Name": "tag:ManagedBy", "Values": ["terraform"]},
            ]
        )
        assert len(response["InternetGateways"]) >= 1, (
            "Runners internet gateway not found. "
            "Run terraform apply in src/api/common/networking/"
        )

    def test_runners_security_group_exists(self, runners_security_group):
        """Verify the runner security group exists."""
        assert runners_security_group is not None, (
            "Runner security group not found. "
            "Run terraform apply in src/api/common/networking/"
        )
