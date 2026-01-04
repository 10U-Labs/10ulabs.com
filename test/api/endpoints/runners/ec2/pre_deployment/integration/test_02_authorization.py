"""Layer 2: Authorization tests.

Verify we have permission to inspect prerequisite resources.
"""
import pytest
from botocore.exceptions import ClientError



def test_can_call_describe_vpcs(ec2_client):
    """Verify we have permission to call EC2 DescribeVpcs."""
    try:
        ec2_client.describe_vpcs(MaxResults=5)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail(
                "No permission to call EC2 DescribeVpcs. "
                "Check IAM policy has ec2:DescribeVpcs."
            )
        raise
    assert True  # Explicit pass


def test_can_call_describe_images(ec2_client):
    """Verify we have permission to call EC2 DescribeImages."""
    try:
        ec2_client.describe_images(Owners=["self"], MaxResults=5)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail(
                "No permission to call EC2 DescribeImages. "
                "Check IAM policy has ec2:DescribeImages."
            )
        raise
    assert True  # Explicit pass


def test_can_call_describe_subnets(ec2_client):
    """Verify we have permission to call EC2 DescribeSubnets."""
    try:
        ec2_client.describe_subnets(MaxResults=5)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail(
                "No permission to call EC2 DescribeSubnets. "
                "Check IAM policy has ec2:DescribeSubnets."
            )
        raise
    assert True  # Explicit pass


def test_can_call_describe_security_groups(ec2_client):
    """Verify we have permission to call EC2 DescribeSecurityGroups."""
    try:
        ec2_client.describe_security_groups(MaxResults=5)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail(
                "No permission to call EC2 DescribeSecurityGroups. "
                "Check IAM policy has ec2:DescribeSecurityGroups."
            )
        raise
    assert True  # Explicit pass
