"""Layer 7: Capability tests for soc_simulations endpoint.

Tests that you can perform required operations. Assumes configuration passed.
"""
import uuid

import pytest

from test_fixtures.integration import Layer7DeploymentCapabilityTests


pytest_plugins = ['test_fixtures.aws']


class TestDeploymentCapability(Layer7DeploymentCapabilityTests):
    """Tests that deployment operations can be performed."""


def test_can_read_from_state_bucket(s3_client, state_bucket_name):
    """Verify can read from Terraform state bucket."""
    response = s3_client.list_objects_v2(
        Bucket=state_bucket_name,
        MaxKeys=1
    )
    can_read = "Contents" in response or "KeyCount" in response
    assert can_read, f"Cannot read from state bucket {state_bucket_name}"


def test_can_write_to_state_bucket(s3_client, state_bucket_name):
    """Verify can write to Terraform state bucket."""
    test_key = f".test/{uuid.uuid4()}.txt"
    try:
        s3_client.put_object(
            Bucket=state_bucket_name,
            Key=test_key,
            Body=b"pre-deployment capability test"
        )
        can_write = True
    finally:
        s3_client.delete_object(Bucket=state_bucket_name, Key=test_key)
    assert can_write, f"Cannot write to state bucket {state_bucket_name}"
