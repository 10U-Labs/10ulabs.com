"""Pytest fixtures for runners/ec2/images endpoint tests."""
import os

import boto3
import pytest


@pytest.fixture(scope="session")
def ec2_client(aws_region):
    """Create an EC2 client."""
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(scope="session")
def test_ami_id():
    """Return the test AMI ID from environment."""
    return os.environ.get("TEST_AMI_ID", "")
