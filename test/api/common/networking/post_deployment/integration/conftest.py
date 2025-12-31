"""Pytest fixtures for api/common/networking post-deployment integration tests.

These tests follow the 3-layer testing model from POST_DEPLOYMENT_INTEGRATION_TESTS.md:
- Layer 1: Existence - Resources were created
- Layer 2: Configuration - Resources configured correctly
- Layer 3: Wiring - Components connected properly

Layer marker system inherited from parent conftest (test/api/common/networking/conftest.py).
"""

import boto3
import pytest

pytest_plugins = ['test_fixtures.aws']


@pytest.fixture(name="ec2_client", scope="module")
def ec2_client_fixture(aws_region):
    """Create an EC2 client for the configured AWS region."""
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(name="runners_vpc", scope="module")
def runners_vpc_fixture(ec2_client):
    """Get the runners VPC, or None if it doesn't exist."""
    response = ec2_client.describe_vpcs(
        Filters=[
            {"Name": "tag:Purpose", "Values": ["runners"]},
            {"Name": "tag:ManagedBy", "Values": ["terraform"]},
        ]
    )
    if not response["Vpcs"]:
        return None
    return response["Vpcs"][0]


@pytest.fixture(name="runners_vpc_id", scope="module")
def runners_vpc_id_fixture(runners_vpc):
    """Get the runners VPC ID."""
    if runners_vpc is None:
        return None
    return runners_vpc["VpcId"]


@pytest.fixture(name="runners_security_group", scope="module")
def runners_security_group_fixture(ec2_client):
    """Get the runner security group, or None if it doesn't exist."""
    response = ec2_client.describe_security_groups(
        Filters=[
            {"Name": "group-name", "Values": ["self-hosted-runner-sg"]},
            {"Name": "tag:Purpose", "Values": ["runners"]},
        ]
    )
    if not response["SecurityGroups"]:
        return None
    return response["SecurityGroups"][0]
