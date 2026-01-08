"""Pytest fixtures for api/common/networking post-deployment E2E tests.

E2E tests verify the networking infrastructure functions as a complete system.
"""
import boto3
import pytest


@pytest.fixture(name="ec2_client", scope="module")
def ec2_client_fixture(aws_region):
    """Create an EC2 client for the configured AWS region."""
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(name="runners_vpc_id", scope="module")
def runners_vpc_id_fixture(ec2_client):
    """Get the runners VPC ID."""
    response = ec2_client.describe_vpcs(
        Filters=[
            {"Name": "tag:Name", "Values": ["TenULabsRunnersVpc"]},
            {"Name": "tag:ManagedBy", "Values": ["terraform"]},
        ]
    )
    vpcs = response.get("Vpcs", [])
    if not vpcs:
        pytest.skip("Runners VPC not found")
    return vpcs[0]["VpcId"]


@pytest.fixture(name="runners_vpc", scope="module")
def runners_vpc_fixture(ec2_client, runners_vpc_id):
    """Get the runners VPC details."""
    response = ec2_client.describe_vpcs(VpcIds=[runners_vpc_id])
    return response["Vpcs"][0]
