"""Layer 6: Capability tests for api/shared/networking pre-deployment.

Tests that you can perform required operations. Assumes configuration passed.

Six-layer testing model:
- Layer 6: Capability - Can perform required operations
"""

from botocore.exceptions import ClientError
import pytest
from test_fixtures.integration import (
    Layer6IAMCapabilityTests,
    Layer6S3CapabilityTests,
    Layer6S3WriteCapabilityTests,
)


pytestmark = pytest.mark.layer(6)


class TestIAMCapabilities(Layer6IAMCapabilityTests):
    """Layer 6: Verify we can perform required IAM operations."""


class TestS3Capabilities(Layer6S3CapabilityTests, Layer6S3WriteCapabilityTests):
    """Layer 6: Verify we can read/write to the terraform state bucket."""

    def test_can_read_state_file(
        self, s3_client, state_bucket_name, networking_state_key
    ):
        """Verify we can read the api_shared_networking state file."""
        try:
            s3_client.head_object(Bucket=state_bucket_name, Key=networking_state_key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "403":
                pytest.fail(
                    f"No permission to read '{networking_state_key}' "
                    f"from '{state_bucket_name}'. "
                    "Check IAM permissions for s3:GetObject."
                )
            if e.response["Error"]["Code"] == "404":
                # State file doesn't exist yet - that's OK for first deployment
                pytest.skip("State file does not exist yet (first deployment)")
            raise
