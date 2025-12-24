"""Pre-deployment integration tests: S3 Prompts Bucket prerequisites.

Verifies that prerequisites for the S3 prompts bucket deployment exist.
This test runs BEFORE terraform apply to ensure dependencies are met.

Five-layer testing model:
- Layer 1: Authentication - Are AWS credentials configured?
- Layer 2: Authorization - Do we have S3 permissions?
"""

import pytest
from botocore.exceptions import ClientError


class TestS3Authentication:
    """Layer 1: Verify AWS credentials can access S3."""

    def test_s3_client_can_list_buckets(self, s3_client):
        """Verify S3 client can make API calls."""
        try:
            response = s3_client.list_buckets()
            assert "Buckets" in response, "S3 list_buckets should return Buckets key"
        except ClientError as err:
            pytest.fail(f"S3 client failed to list buckets: {err}")


class TestS3Authorization:
    """Layer 2: Verify we have permission to create S3 resources."""

    def test_can_call_s3_head_bucket(self, s3_client, s3_prompts_bucket_name):
        """Verify we have permission to check bucket existence."""
        # This will either succeed (bucket exists) or fail with 404 (doesn't exist)
        # Both are acceptable - we just need to verify we have API access
        try:
            s3_client.head_bucket(Bucket=s3_prompts_bucket_name)
        except ClientError as err:
            code = err.response["Error"]["Code"]
            # 404 means bucket doesn't exist (expected pre-deployment)
            # 403 means no permission (test failure)
            if code == "403":
                pytest.fail(
                    f"No permission to access S3 bucket '{s3_prompts_bucket_name}'. "
                    "Check IAM permissions."
                )
            # 404 is expected if bucket doesn't exist yet
            assert code in ("404", "NoSuchBucket"), f"Unexpected error: {code}"
