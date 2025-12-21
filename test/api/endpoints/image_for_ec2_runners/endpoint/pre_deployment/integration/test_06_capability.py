"""Layer 6: Capability - Verify we can perform required operations.

These tests verify that you can perform the operations required for deployment.
Assumes configuration (Layer 5) has passed.

Per the tenets, capability tests should clean up any test artifacts in finally blocks.
"""
import pytest

pytestmark = pytest.mark.layer(6)


class TestEC2Capabilities:
    """Layer 6: Verify we can perform EC2 operations required for deployment."""

    def test_can_describe_images_with_self_owner(self, ec2_client):
        """Verify we can describe our own AMIs."""
        response = ec2_client.describe_images(Owners=["self"], MaxResults=5)
        assert "Images" in response

    def test_can_describe_images_with_filters(self, ec2_client):
        """Verify we can describe images with filters."""
        response = ec2_client.describe_images(
            Owners=["self"],
            Filters=[{"Name": "state", "Values": ["available"]}],
            MaxResults=5,
        )
        assert "Images" in response
