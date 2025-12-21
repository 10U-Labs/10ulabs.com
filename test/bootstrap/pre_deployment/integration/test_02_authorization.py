"""Layer 2: Authorization tests for bootstrap pre-deployment validation.

Verify permission to inspect the state bucket (not existence, not capability).
"""
import pytest
from botocore.exceptions import ClientError


def test_can_call_s3_head_bucket(s3_client, state_bucket_name):
    """Verify permission to call s3:HeadBucket on state bucket."""
    try:
        s3_client.head_bucket(Bucket=state_bucket_name)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ("403", "AccessDenied"):
            pytest.fail(f"No permission to call s3:HeadBucket on '{state_bucket_name}'")
        # 404 means bucket doesn't exist but we have permission to check - OK
        if error_code != "404":
            raise


def test_can_call_s3_get_object(s3_client, state_bucket_name):
    """Verify permission to call s3:GetObject on state bucket."""
    try:
        s3_client.get_object(Bucket=state_bucket_name, Key="bootstrap/terraform.tfstate")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ("403", "AccessDenied"):
            pytest.fail(f"No permission to call s3:GetObject on '{state_bucket_name}'")
        # NoSuchKey/NoSuchBucket means object/bucket doesn't exist but we have permission
        if error_code not in ("NoSuchKey", "NoSuchBucket", "404"):
            raise
