"""Layer 2: Authorization tests.

These tests verify that the current credentials have permission to INSPECT
prerequisite resources. Not existence, not capability - just the ability
to describe/inspect resources.

If a resource doesn't exist, that's OK at this layer - we have permission
to check. Existence is verified in Layer 3.
"""
import pytest
from botocore.exceptions import ClientError


def test_can_describe_iam_instance_profile(iam_client, config):
    """Verify permission to inspect IAM instance profile."""
    profile_name = config.get("github_runner_iam_instance_profile_name", "")
    if not profile_name:
        pytest.skip("github_runner_iam_instance_profile_name not configured")

    try:
        iam_client.get_instance_profile(InstanceProfileName=profile_name)
    except iam_client.exceptions.NoSuchEntityException:
        pass  # Resource doesn't exist, but we have permission to check
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail(f"No permission to inspect IAM instance profile '{profile_name}'")
        raise
    assert True  # Explicit pass


def test_can_describe_security_groups(ec2_client, security_group_id):
    """Verify permission to inspect security groups."""
    if not security_group_id:
        pytest.skip("No security group ID configured")

    try:
        ec2_client.describe_security_groups(GroupIds=[security_group_id])
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to inspect security group '{security_group_id}'")
        if error_code == "InvalidGroup.NotFound":
            pass  # Resource doesn't exist, but we have permission to check
        else:
            raise
    assert True  # Explicit pass


def test_can_describe_subnets(ec2_client, subnet_ids):
    """Verify permission to inspect subnets."""
    if not subnet_ids:
        pytest.skip("No subnet IDs configured")

    try:
        ec2_client.describe_subnets(SubnetIds=subnet_ids)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to inspect subnets: {subnet_ids}")
        if error_code == "InvalidSubnetID.NotFound":
            pass  # Resource doesn't exist, but we have permission to check
        else:
            raise
    assert True  # Explicit pass


def test_can_describe_images(ec2_client):
    """Verify permission to describe EC2 images."""
    try:
        # Just verify we can call describe_images - don't need specific AMI
        # Note: AWS requires MaxResults >= 5 for describe_images
        ec2_client.describe_images(
            Filters=[{"Name": "state", "Values": ["available"]}],
            MaxResults=5,
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail("No permission to describe EC2 images")
        raise
    assert True  # Explicit pass


def test_can_describe_instance_types(ec2_client, instance_types):
    """Verify permission to describe instance types."""
    if not instance_types:
        pytest.skip("No instance types configured")

    try:
        ec2_client.describe_instance_types(InstanceTypes=instance_types[:1])
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to describe instance types: {instance_types}")
        if error_code == "InvalidInstanceType":
            pass  # Invalid type, but we have permission to check
        else:
            raise
    assert True  # Explicit pass
