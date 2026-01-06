"""Layer 7: Capability tests for sessions endpoint.

Capability tests verify that you can perform required operations.
These test that deployment prerequisites allow required actions.
"""
import uuid

import pytest
from botocore.exceptions import ClientError


pytestmark = pytest.mark.layer(7)


class TestTerraformStateCapability:
    """Tests for Terraform state access capability."""

    def test_can_read_terraform_state(self, s3_client, state_bucket_name):
        """Verify can read from Terraform state bucket."""
        has_capability = True
        try:
            s3_client.list_objects_v2(
                Bucket=state_bucket_name,
                MaxKeys=1
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                has_capability = False
            else:
                raise
        assert has_capability, (
            f"No permission to read from state bucket '{state_bucket_name}'. "
            "Check IAM permissions for s3:ListBucket."
        )
