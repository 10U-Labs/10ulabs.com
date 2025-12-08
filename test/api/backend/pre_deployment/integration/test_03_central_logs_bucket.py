"""Tests to validate central logs bucket before api_backend deployment.

These tests MUST run after test_01 and test_02 because they depend on:
- Valid AWS credentials (test_01)
- Ability to access terraform state (test_02) to read bootstrap outputs

Five-layer testing model:
- Layer 2: Authorization - Can we call the API?
- Layer 3: Existence - Do bootstrap outputs exist? Does the bucket exist?
- Layer 5: Capability - Can we write to the bucket?

api_backend uses Firehose to deliver logs to this bucket.
"""

import uuid

from botocore.exceptions import ClientError
import pytest


class TestBootstrapOutputsExistence:
    """Layer 1: Verify bootstrap terraform outputs exist."""

    def test_01_bootstrap_initialized(self, bootstrap_initialized):
        """Verify terraform init succeeds for bootstrap."""
        assert bootstrap_initialized, (
            "Terraform init failed for src/bootstrap/. "
            "Check AWS credentials and S3 backend configuration."
        )

    def test_02_central_logs_bucket_arn_output_exists(self, bootstrap_outputs):
        """Verify arn_for_central_logs_bucket output exists."""
        arn = bootstrap_outputs.get("arn_for_central_logs_bucket")
        assert arn, (
            "arn_for_central_logs_bucket output not found in bootstrap. "
            "Check src/bootstrap/outputs.tf"
        )

    def test_03_github_actions_role_arn_output_exists(self, bootstrap_outputs):
        """Verify arn_for_github_actions_role output exists."""
        arn = bootstrap_outputs.get("arn_for_github_actions_role")
        assert arn, (
            "arn_for_github_actions_role output not found in bootstrap. "
            "Check src/bootstrap/outputs.tf"
        )


class TestCentralLogsBucketExistence:
    """Layer 1: Verify the central logs bucket exists."""

    def test_01_bucket_name_extracted(self, central_logs_bucket_name):
        """Verify central logs bucket name was extracted from ARN."""
        assert central_logs_bucket_name, (
            "Could not extract bucket name from arn_for_central_logs_bucket. "
            "Check bootstrap outputs."
        )

    def test_02_can_call_head_bucket_api(self, s3_client, central_logs_bucket_name):
        """Verify we have permission to call s3:HeadBucket on central logs."""
        if not central_logs_bucket_name:
            pytest.skip("central_logs_bucket_name not available")
        try:
            s3_client.head_bucket(Bucket=central_logs_bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "403":
                pytest.fail(
                    f"No permission to call HeadBucket on '{central_logs_bucket_name}'. "
                    "Check IAM permissions for s3:HeadBucket."
                )
            if e.response["Error"]["Code"] == "404":
                pytest.fail(f"Central logs bucket '{central_logs_bucket_name}' does not exist.")
            raise

    def test_03_bucket_exists(self, s3_client, central_logs_bucket_name):
        """Verify the central logs bucket exists."""
        if not central_logs_bucket_name:
            pytest.skip("central_logs_bucket_name not available")
        try:
            response = s3_client.head_bucket(Bucket=central_logs_bucket_name)
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                pytest.fail(
                    f"Central logs bucket '{central_logs_bucket_name}' does not exist. "
                    "Run terraform apply in src/bootstrap/"
                )
            raise


class TestCentralLogsBucketCapability:
    """Layer 5: Verify we can write to the central logs bucket."""

    def test_01_can_put_object(self, s3_client, central_logs_bucket_name):
        """Verify we can write to the central logs bucket (needed for Firehose)."""
        if not central_logs_bucket_name:
            pytest.skip("central_logs_bucket_name not available")
        object_key = f"pre-deployment-test/{uuid.uuid4()}"
        bucket = central_logs_bucket_name
        try:
            s3_client.put_object(Bucket=bucket, Key=object_key, Body=b"test-write")
        except ClientError as err:
            error_code = err.response["Error"]["Code"]
            if error_code == "AccessDenied":
                pytest.fail(
                    f"No permission to write to '{bucket}'. "
                    "Firehose delivery will fail without write access. "
                    "Check IAM permissions for s3:PutObject."
                )
            raise
        finally:
            try:
                s3_client.delete_object(Bucket=bucket, Key=object_key)
            except ClientError:
                pass

    def test_02_can_delete_object(self, s3_client, central_logs_bucket_name):
        """Verify we can delete from the central logs bucket (needed for cleanup)."""
        if not central_logs_bucket_name:
            pytest.skip("central_logs_bucket_name not available")
        object_key = f"pre-deployment-test/{uuid.uuid4()}"
        bucket = central_logs_bucket_name
        try:
            s3_client.put_object(Bucket=bucket, Key=object_key, Body=b"test-delete")
            s3_client.delete_object(Bucket=bucket, Key=object_key)
        except ClientError as err:
            error_code = err.response["Error"]["Code"]
            if error_code == "AccessDenied":
                pytest.fail(
                    f"No permission to delete from '{bucket}'. "
                    "Check IAM permissions for s3:DeleteObject."
                )
            raise
