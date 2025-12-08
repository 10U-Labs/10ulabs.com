"""Tests to validate terraform state bucket before api_backend deployment.

These tests MUST run after test_01_iam_role.py because they depend on having
valid AWS credentials and IAM permissions.

Five-layer testing model:
- Layer 2: Authorization - Can we call the API?
- Layer 3: Existence - Does the bucket exist?
- Layer 5: Capability - Can we read/write to the bucket?

api_backend stores its terraform state in this bucket at key 'api/terraform.tfstate'.
"""

import uuid

from botocore.exceptions import ClientError
import pytest


class TestTerraformStateBucketExistence:
    """Layer 1: Verify the terraform state bucket exists."""

    def test_01_can_call_head_bucket_api(self, s3_client, state_bucket_name):
        """Verify we have permission to call s3:HeadBucket."""
        try:
            s3_client.head_bucket(Bucket=state_bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "403":
                pytest.fail(
                    f"No permission to call HeadBucket on '{state_bucket_name}'. "
                    "Check IAM permissions for s3:HeadBucket."
                )
            if e.response["Error"]["Code"] == "404":
                pytest.fail(f"Terraform state bucket '{state_bucket_name}' does not exist.")
            raise

    def test_02_bucket_exists(self, s3_client, state_bucket_name):
        """Verify the terraform state bucket exists."""
        try:
            response = s3_client.head_bucket(Bucket=state_bucket_name)
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                pytest.fail(
                    f"Terraform state bucket '{state_bucket_name}' does not exist. "
                    "Run terraform apply in src/bootstrap/"
                )
            raise


class TestTerraformStateBucketCapability:
    """Layer 3: Verify we can read/write to the terraform state bucket."""

    def test_01_can_list_objects(self, s3_client, state_bucket_name):
        """Verify we can list objects in the state bucket."""
        try:
            s3_client.list_objects_v2(Bucket=state_bucket_name, MaxKeys=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to list objects in '{state_bucket_name}'. "
                    "Check IAM permissions for s3:ListBucket."
                )
            raise

    def test_02_can_get_object(self, s3_client, state_bucket_name):
        """Verify we can read the api_backend state file."""
        state_key = "api/terraform.tfstate"
        try:
            s3_client.head_object(Bucket=state_bucket_name, Key=state_key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "403":
                pytest.fail(
                    f"No permission to read '{state_key}' from '{state_bucket_name}'. "
                    "Check IAM permissions for s3:GetObject."
                )
            if e.response["Error"]["Code"] == "404":
                # State file doesn't exist yet - that's OK for first deployment
                pytest.skip("State file does not exist yet (first deployment)")
            raise

    def test_03_can_put_object(self, s3_client, state_bucket_name):
        """Verify we can write to the state bucket."""
        test_key = f".pre-deployment-test/{uuid.uuid4()}"
        try:
            s3_client.put_object(
                Bucket=state_bucket_name,
                Key=test_key,
                Body=b"pre-deployment-test"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to write to '{state_bucket_name}'. "
                    "Check IAM permissions for s3:PutObject."
                )
            raise
        finally:
            try:
                s3_client.delete_object(Bucket=state_bucket_name, Key=test_key)
            except ClientError:
                pass

    def test_04_can_delete_object(self, s3_client, state_bucket_name):
        """Verify we can delete objects from the state bucket."""
        test_key = f".pre-deployment-test/{uuid.uuid4()}"
        try:
            s3_client.put_object(
                Bucket=state_bucket_name,
                Key=test_key,
                Body=b"pre-deployment-test"
            )
            s3_client.delete_object(Bucket=state_bucket_name, Key=test_key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to delete from '{state_bucket_name}'. "
                    "Check IAM permissions for s3:DeleteObject."
                )
            raise
