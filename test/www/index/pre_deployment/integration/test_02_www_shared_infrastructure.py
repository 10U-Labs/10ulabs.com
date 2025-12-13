"""Tests to validate www_shared infrastructure exists for www index.

Five-layer testing model:
- Layer 3: Existence - Do the S3 bucket and CloudFront distribution exist?

These tests verify that www_shared resources this endpoint depends on exist.
"""

from botocore.exceptions import ClientError
import pytest


class TestWWWSharedOutputs:
    """Layer 3: Verify www_shared terraform outputs are accessible."""

    def test_bucket_name_output_exists(self, www_shared_outputs):
        """Verify bucket_name output is available."""
        assert www_shared_outputs.get("bucket_name"), (
            "bucket_name output not found in www_shared. "
            "Run terraform apply in src/www/shared/"
        )

    def test_website_domain_name_output_exists(self, www_shared_outputs):
        """Verify website_domain_name output is available."""
        assert www_shared_outputs.get("website_domain_name"), (
            "website_domain_name output not found in www_shared. "
            "Run terraform apply in src/www/shared/"
        )

    def test_cloudfront_distribution_id_output_exists(self, www_shared_outputs):
        """Verify cloudfront_distribution_id output is available."""
        assert www_shared_outputs.get("cloudfront_distribution_id"), (
            "cloudfront_distribution_id output not found in www_shared. "
            "Run terraform apply in src/www/shared/"
        )


class TestS3AndCloudFront:
    """Layer 3: Verify S3 bucket and CloudFront distribution exist."""

    def test_s3_bucket_exists(self, s3_client, www_shared_outputs):
        """Verify the S3 bucket exists in AWS."""
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

    def test_cloudfront_distribution_exists(self, cloudfront_client, www_shared_outputs):
        """Verify the CloudFront distribution exists in AWS."""
        distribution_id = www_shared_outputs.get("cloudfront_distribution_id")
        if not distribution_id:
            pytest.skip("cloudfront_distribution_id output not available")
        try:
            response = cloudfront_client.get_distribution(Id=distribution_id)
            assert response["Distribution"]["Id"] == distribution_id, (
                f"Distribution ID mismatch: expected {distribution_id}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchDistribution":
                pytest.fail(
                    f"CloudFront distribution '{distribution_id}' does not exist. "
                    "Run terraform apply in src/www/shared/"
                )
            raise

    def test_cloudfront_distribution_is_deployed(self, cloudfront_client, www_shared_outputs):
        """Verify the CloudFront distribution is deployed."""
        distribution_id = www_shared_outputs.get("cloudfront_distribution_id")
        if not distribution_id:
            pytest.skip("cloudfront_distribution_id output not available")
        try:
            response = cloudfront_client.get_distribution(Id=distribution_id)
            status = response["Distribution"]["Status"]
            assert status == "Deployed", (
                f"CloudFront distribution '{distribution_id}' is not deployed (status: {status}). "
                "Wait for distribution to finish deploying."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchDistribution":
                pytest.skip("Distribution does not exist")
            raise
