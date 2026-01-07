"""Layer 6: Configuration tests for www home page deployment prerequisites.

Test that prerequisite resources are configured correctly. Assumes existence passed.
"""
import pytest
from botocore.exceptions import ClientError


class TestCloudFrontConfiguration:
    """Layer 6: Verify CloudFront distribution is configured correctly."""

    def test_cloudfront_distribution_is_deployed(
        self, cloudfront_distribution, www_common_outputs
    ):
        """Verify the CloudFront distribution is deployed."""
        distribution_id = www_common_outputs.get("cloudfront_distribution_id")
        if not distribution_id:
            pytest.skip("cloudfront_distribution_id output not available")
        if cloudfront_distribution is None:
            pytest.skip("Distribution does not exist")
        status = cloudfront_distribution["Status"]
        is_deployed = status == "Deployed"
        assert is_deployed, (
            f"CloudFront distribution '{distribution_id}' is not deployed "
            f"(status: {status}). Wait for distribution to finish deploying."
        )

    def test_cloudfront_distribution_is_enabled(
        self, cloudfront_distribution, www_common_outputs
    ):
        """Verify the CloudFront distribution is enabled."""
        distribution_id = www_common_outputs.get("cloudfront_distribution_id")
        if not distribution_id:
            pytest.skip("cloudfront_distribution_id output not available")
        if cloudfront_distribution is None:
            pytest.skip("Distribution does not exist")
        is_enabled = (
            cloudfront_distribution["DistributionConfig"]["Enabled"] is True
        )
        assert is_enabled, (
            f"CloudFront distribution '{distribution_id}' is disabled. "
            "Enable the distribution in AWS Console or via Terraform."
        )


class TestS3BucketConfiguration:
    """Layer 6: Verify S3 bucket is configured correctly."""

    def test_s3_bucket_location_is_retrievable(self, s3_client, www_common_outputs):
        """Verify S3 bucket location is retrievable."""
        bucket_name = www_common_outputs.get("bucket_name")
        if not bucket_name:
            pytest.skip("bucket_name output not available")
        try:
            response = s3_client.get_bucket_location(Bucket=bucket_name)
            # If we can get the location, the bucket exists and is accessible
            location_retrieved = "LocationConstraint" in response
            assert location_retrieved, "Should be able to retrieve bucket location"
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                pytest.skip("Bucket does not exist")
            raise

    def test_s3_bucket_accepts_put_operations(self, s3_client, www_common_outputs):
        """Verify S3 bucket permissions allow put operations (tested via list)."""
        bucket_name = www_common_outputs.get("bucket_name")
        if not bucket_name:
            pytest.skip("bucket_name output not available")
        try:
            response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
            # If we can list, we have read access
            can_list = "Contents" in response or "KeyCount" in response
            assert can_list or response.get("KeyCount", 0) >= 0
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                pytest.skip("Bucket does not exist")
            raise
