"""Tests to validate terraform state bucket before api_shared_runners deployment.

These tests MUST run after test_01_aws_credentials.py because they depend on having
valid AWS credentials and IAM permissions.

Five-layer testing model:
- Layer 2: Authorization - Can we call the API?
- Layer 3: Existence - Does the bucket exist?
- Layer 4: Configuration - Is the bucket configured correctly?
- Layer 5: Capability - Can we read/write to the bucket?

api_shared_runners stores its terraform state in this bucket at key
'api/shared/runners/terraform.tfstate'.
"""
import uuid

from botocore.exceptions import ClientError
import pytest


class TestTerraformStateBucketExistence:
    """Layer 3: Verify the terraform state bucket exists."""

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


class TestTerraformStateBucketConfiguration:
    """Layer 4: Verify the terraform state bucket is configured correctly."""

    def test_01_encryption_enabled(self, s3_client, state_bucket_name):
        """Verify bucket encryption is enabled."""
        try:
            response = s3_client.get_bucket_encryption(Bucket=state_bucket_name)
            rules = response.get("ServerSideEncryptionConfiguration", {}).get("Rules", [])
            assert len(rules) > 0, (
                f"Bucket '{state_bucket_name}' has no encryption rules configured. "
                "Terraform state buckets should have server-side encryption enabled."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.skip(
                    f"No permission to check encryption on '{state_bucket_name}'. "
                    "Check IAM permissions for s3:GetEncryptionConfiguration."
                )
            if e.response["Error"]["Code"] == "ServerSideEncryptionConfigurationNotFoundError":
                pytest.fail(
                    f"Bucket '{state_bucket_name}' has no encryption configured. "
                    "Terraform state buckets should have server-side encryption enabled."
                )
            raise

    def test_03_bucket_in_expected_region(self, s3_client, state_bucket_name, state_bucket_region):
        """Verify bucket is in the expected region."""
        try:
            response = s3_client.get_bucket_location(Bucket=state_bucket_name)
            # AWS returns None for us-east-1, otherwise the region name
            location = response.get("LocationConstraint")
            actual_region = location if location else "us-east-1"
            assert actual_region == state_bucket_region, (
                f"Bucket '{state_bucket_name}' is in region '{actual_region}', "
                f"expected '{state_bucket_region}'."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.skip(
                    f"No permission to check location of '{state_bucket_name}'. "
                    "Check IAM permissions for s3:GetBucketLocation."
                )
            raise


class TestTerraformStateBucketCapability:
    """Layer 5: Verify we can read/write to the terraform state bucket."""

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

    def test_02_can_get_object(self, s3_client, state_bucket_name, runners_state_key):
        """Verify we can read the api_shared_runners state file."""
        try:
            s3_client.head_object(Bucket=state_bucket_name, Key=runners_state_key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "403":
                pytest.fail(
                    f"No permission to read '{runners_state_key}' from '{state_bucket_name}'. "
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
        finally:
            try:
                s3_client.delete_object(Bucket=state_bucket_name, Key=test_key)
            except ClientError:
                pass
