"""Tests to validate www_shared infrastructure exists for www index.

Five-layer testing model:
- Layer 3: Existence - Do the S3 bucket and CloudFront distribution exist?

These tests verify that www_shared resources this endpoint depends on exist.
"""

from botocore.exceptions import ClientError
import pytest
from test_fixtures.integration import create_www_shared_s3_existence_tests


# Use shared S3 bucket existence tests
TestWWWSharedS3 = create_www_shared_s3_existence_tests()


class TestWWWSharedOutputs:
    """Layer 3: Verify www_shared terraform outputs are accessible."""

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


class TestCloudFrontDistribution:
    """Layer 3: Verify CloudFront distribution exists and is deployed."""

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
