"""Tests to validate S3 terraform state bucket before workflow_fixer deployment.

Five-layer testing model:
- Layer 2: Authorization - Can we call S3 APIs?
- Layer 3: Existence - Does the bucket exist?
- Layer 5: Capability - Can we read/write terraform state?
"""

from botocore.exceptions import ClientError
import pytest


class TestS3BucketAuthorization:
    """Layer 2: Verify we can call S3 APIs."""

    def test_01_can_call_head_bucket_api(self, s3_client, state_bucket_name):
        """Verify we have permission to call s3:HeadBucket."""
        try:
            s3_client.head_bucket(Bucket=state_bucket_name)
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "403":
                pytest.fail(
                    f"No permission to call HeadBucket on '{state_bucket_name}'. "
                    "Check IAM permissions for s3:HeadBucket."
                )
            if code == "404":
                pass  # Existence check is in next layer
            else:
                raise


class TestS3BucketExistence:
    """Layer 3: Verify the S3 bucket exists."""

    def test_01_bucket_exists(self, s3_client, state_bucket_name):
        """Verify the terraform state bucket exists."""
        try:
            s3_client.head_bucket(Bucket=state_bucket_name)
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "404":
                pytest.fail(
                    f"S3 bucket '{state_bucket_name}' does not exist. "
                    "Run terraform apply in src/bootstrap/"
                )
            if code == "403":
                pytest.skip("Cannot verify bucket existence - access denied")
            raise


class TestS3BucketCapability:
    """Layer 5: Verify we can perform required S3 operations."""

    def test_01_can_list_objects(self, s3_client, state_bucket_name):
        """Verify we can list objects in the bucket."""
        try:
            s3_client.list_objects_v2(Bucket=state_bucket_name, MaxKeys=1)
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to list objects in '{state_bucket_name}'. "
                    "Check IAM permissions for s3:ListBucket."
                )
            raise

    def test_02_can_put_object(self, s3_client, state_bucket_name):
        """Verify we can write objects to the bucket."""
        test_key = "test/workflow_fixer_pre_deployment_test.txt"
        try:
            s3_client.put_object(
                Bucket=state_bucket_name,
                Key=test_key,
                Body=b"pre-deployment test",
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to put objects in '{state_bucket_name}'. "
                    "Check IAM permissions for s3:PutObject."
                )
            raise
        finally:
            # Clean up test object
            try:
                s3_client.delete_object(Bucket=state_bucket_name, Key=test_key)
            except ClientError:
                pass

    def test_03_can_get_object(self, s3_client, state_bucket_name):
        """Verify we can read objects from the bucket."""
        test_key = "test/workflow_fixer_pre_deployment_test_read.txt"
        try:
            # First put an object
            s3_client.put_object(
                Bucket=state_bucket_name,
                Key=test_key,
                Body=b"pre-deployment test read",
            )
            # Then try to read it
            s3_client.get_object(Bucket=state_bucket_name, Key=test_key)
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to get objects from '{state_bucket_name}'. "
                    "Check IAM permissions for s3:GetObject."
                )
            raise
        finally:
            # Clean up test object
            try:
                s3_client.delete_object(Bucket=state_bucket_name, Key=test_key)
            except ClientError:
                pass
