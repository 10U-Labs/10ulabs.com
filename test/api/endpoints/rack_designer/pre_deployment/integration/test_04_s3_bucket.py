"""Tests to validate S3 bucket exists for rack_designer designs.

Five-layer testing model:
- Layer 3: Existence - Does the S3 bucket exist?

These tests verify that www_shared resources this endpoint depends on exist.
"""

from botocore.exceptions import ClientError
import pytest


class TestS3Bucket:
    """Layer 3: Verify www_shared outputs and S3 bucket exist."""

    def test_bucket_name_output_exists(self, www_shared_outputs):
        """Verify bucket_name output is available."""
        assert www_shared_outputs.get("bucket_name"), (
            "bucket_name output not found in www_shared. "
            "Run terraform apply in src/www/shared/"
        )

    def test_s3_bucket_exists(self, s3_client, www_shared_outputs):
        """Verify the S3 bucket for designs exists."""
        bucket_name = www_shared_outputs.get("bucket_name")
        if not bucket_name:
            pytest.skip("bucket_name output not available")
        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                pytest.fail(
                    f"S3 bucket '{bucket_name}' does not exist. "
                    "Run terraform apply in src/www/shared/"
                )
            raise
