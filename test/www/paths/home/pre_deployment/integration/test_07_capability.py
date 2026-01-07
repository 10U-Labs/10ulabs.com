"""Layer 7: Capability tests for www home page deployment.

Test that you can perform required deployment operations.
Assumes configuration passed.
"""
import uuid

import pytest
from botocore.exceptions import ClientError


class TestS3WriteCapability:
    """Layer 7: Verify can write to S3 bucket for deployment."""

    def test_can_write_to_s3_bucket(self, s3_client, www_common_outputs):
        """Verify can write objects to the website S3 bucket."""
        bucket_name = www_common_outputs.get("bucket_name")
        if not bucket_name:
            pytest.skip("bucket_name output not available")
        test_key = f"home/.pre-deployment-test/{uuid.uuid4()}.txt"
        try:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=b"pre-deployment test",
                ContentType="text/plain"
            )
            write_succeeded = True
            assert write_succeeded, "Write should succeed"
        except ClientError as e:
            pytest.fail(
                f"Cannot write to S3 bucket '{bucket_name}': {e.response['Error']}"
            )
        finally:
            try:
                s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            except ClientError:
                pass  # Best effort cleanup

    def test_can_delete_from_s3_bucket(self, s3_client, www_common_outputs):
        """Verify can delete objects from the website S3 bucket."""
        bucket_name = www_common_outputs.get("bucket_name")
        if not bucket_name:
            pytest.skip("bucket_name output not available")
        test_key = f"home/.pre-deployment-test/{uuid.uuid4()}.txt"
        try:
            # First create an object
            s3_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=b"pre-deployment test"
            )
            # Then delete it
            s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            delete_succeeded = True
            assert delete_succeeded, "Delete should succeed"
        except ClientError as e:
            pytest.fail(
                f"Cannot delete from S3 bucket '{bucket_name}': {e.response['Error']}"
            )


class TestCloudFrontInvalidationCapability:
    """Layer 7: Verify can create CloudFront invalidations."""

    def test_can_list_invalidations(self, cloudfront_client, www_common_outputs):
        """Verify can list CloudFront invalidations."""
        distribution_id = www_common_outputs.get("cloudfront_distribution_id")
        if not distribution_id:
            pytest.skip("cloudfront_distribution_id output not available")
        try:
            response = cloudfront_client.list_invalidations(
                DistributionId=distribution_id,
                MaxItems="1"
            )
            can_list = "InvalidationList" in response
            assert can_list, "Should be able to list invalidations"
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"Cannot list CloudFront invalidations for '{distribution_id}'"
                )
            if e.response["Error"]["Code"] == "NoSuchDistribution":
                pytest.skip("Distribution does not exist")
            raise

    def test_can_get_distribution_config(self, cloudfront_client, www_common_outputs):
        """Verify can get CloudFront distribution config."""
        distribution_id = www_common_outputs.get("cloudfront_distribution_id")
        if not distribution_id:
            pytest.skip("cloudfront_distribution_id output not available")
        try:
            response = cloudfront_client.get_distribution_config(Id=distribution_id)
            can_get_config = "DistributionConfig" in response
            assert can_get_config, "Should be able to get distribution config"
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"Cannot get CloudFront config for '{distribution_id}'"
                )
            if e.response["Error"]["Code"] == "NoSuchDistribution":
                pytest.skip("Distribution does not exist")
            raise
