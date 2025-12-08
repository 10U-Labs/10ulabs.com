"""S3 state bucket test battery for www_shared pre-deployment validation.

Tests are ordered to fail fast with maximum diagnostic granularity:
1. Bucket existence verification
2. Read capability (HeadBucket, ListObjects, GetObject)
3. Write capability (PutObject, DeleteObject)
"""
import uuid

import pytest
from botocore.exceptions import ClientError


class TestBucketExistence:
    """Layer 1: Verify the S3 state bucket exists."""

    def test_01_can_call_s3_head_bucket_api(self, s3_client, state_bucket_name):
        """Verify we have permission to call s3:HeadBucket."""
        try:
            s3_client.head_bucket(Bucket=state_bucket_name)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("403", "AccessDenied"):
                pytest.fail(
                    f"No permission to call s3:HeadBucket on '{state_bucket_name}'"
                )
            raise

    def test_02_state_bucket_exists(self, s3_client, state_bucket_name):
        """Verify the terraform state bucket exists."""
        try:
            response = s3_client.head_bucket(Bucket=state_bucket_name)
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                pytest.fail(f"State bucket '{state_bucket_name}' does not exist")
            raise


class TestReadCapability:
    """Layer 3a: Verify we can read from the state bucket."""

    def test_01_can_list_objects(self, s3_client, state_bucket_name):
        """Verify we can call s3:ListObjectsV2."""
        try:
            response = s3_client.list_objects_v2(
                Bucket=state_bucket_name,
                MaxKeys=1
            )
            assert "Contents" in response or "KeyCount" in response
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDenied":
                pytest.fail(
                    f"No permission to call s3:ListObjectsV2 on '{state_bucket_name}'"
                )
            raise

    def test_02_can_get_object(self, s3_client, state_bucket_name):
        """Verify we can call s3:GetObject on a state file."""
        try:
            response = s3_client.list_objects_v2(
                Bucket=state_bucket_name,
                MaxKeys=1
            )
            if not response.get("Contents"):
                pytest.skip("No objects in bucket to test GetObject")
            key = response["Contents"][0]["Key"]
            obj_response = s3_client.get_object(Bucket=state_bucket_name, Key=key)
            assert obj_response["ResponseMetadata"]["HTTPStatusCode"] == 200
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDenied":
                pytest.fail(
                    f"No permission to call s3:GetObject on '{state_bucket_name}'"
                )
            raise


class TestWriteCapability:
    """Layer 3b: Verify we can write to the state bucket."""

    @pytest.fixture
    def test_object_key(self):
        """Generate a unique test object key."""
        return f".pre-deployment-test/{uuid.uuid4()}.txt"

    def test_01_can_put_object(self, s3_client, state_bucket_name, test_object_key):
        """Verify we can call s3:PutObject."""
        try:
            response = s3_client.put_object(
                Bucket=state_bucket_name,
                Key=test_object_key,
                Body=b"pre-deployment capability test"
            )
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDenied":
                pytest.fail(
                    f"No permission to call s3:PutObject on '{state_bucket_name}'"
                )
            raise
        finally:
            try:
                s3_client.delete_object(Bucket=state_bucket_name, Key=test_object_key)
            except ClientError:
                pass

    def test_02_can_delete_object(self, s3_client, state_bucket_name, test_object_key):
        """Verify we can call s3:DeleteObject."""
        try:
            s3_client.put_object(
                Bucket=state_bucket_name,
                Key=test_object_key,
                Body=b"pre-deployment capability test"
            )
            response = s3_client.delete_object(
                Bucket=state_bucket_name,
                Key=test_object_key
            )
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 204
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDenied":
                pytest.fail(
                    f"No permission to call s3:DeleteObject on '{state_bucket_name}'"
                )
            raise
