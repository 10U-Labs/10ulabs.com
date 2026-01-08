"""Layer 2: Authorization tests for api/common/networking pre-deployment.

Tests that credentials have permission to INSPECT prerequisite resources.
Not existence, not capability - just permission to check.

Six-layer testing model:
- Layer 2: Authorization - Permission to inspect resources
"""

from botocore.exceptions import ClientError
import pytest
from test_fixtures.integration import (
    Layer2IAMAuthorizationTests,
    Layer2S3AuthorizationTests,
)




class TestIAMRoleInspectionAuthorization(Layer2IAMAuthorizationTests):
    """Layer 2: Verify permission to inspect IAM roles."""


class TestS3BucketInspectionAuthorization(Layer2S3AuthorizationTests):
    """Layer 2: Verify permission to inspect S3 buckets."""

    def test_can_call_s3_get_bucket_encryption_api(
        self, s3_client, state_bucket_name
    ):
        """Verify we have permission to call s3:GetEncryptionConfiguration."""
        try:
            s3_client.get_bucket_encryption(Bucket=state_bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to check encryption on '{state_bucket_name}'. "
                    "Check IAM permissions for s3:GetEncryptionConfiguration."
                )
            # Other errors (404, ServerSideEncryptionConfigurationNotFoundError)
            # mean we have permission to check
            if e.response["Error"]["Code"] not in (
                "404",
                "ServerSideEncryptionConfigurationNotFoundError",
                "NoSuchBucket",
            ):
                raise
        assert True  # Explicit pass

    def test_can_call_s3_get_bucket_location_api(
        self, s3_client, state_bucket_name
    ):
        """Verify we have permission to call s3:GetBucketLocation."""
        try:
            s3_client.get_bucket_location(Bucket=state_bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to check location of '{state_bucket_name}'. "
                    "Check IAM permissions for s3:GetBucketLocation."
                )
            if e.response["Error"]["Code"] not in ("404", "NoSuchBucket"):
                raise
        assert True  # Explicit pass
