"""Tests to validate www_common infrastructure exists for www index.

Five-layer testing model:
- Layer 3: Existence - Do the S3 bucket and CloudFront distribution exist?

These tests verify that www_common resources this endpoint depends on exist.
"""

from botocore.exceptions import ClientError
import pytest
from test_fixtures.integration import create_www_common_s3_existence_tests


# Use common S3 bucket existence tests
TestWWWCommonS3 = create_www_common_s3_existence_tests()


class TestWWWCommonOutputs:
    """Layer 3: Verify www_common terraform outputs are accessible."""

    def test_website_domain_name_output_exists(self, www_common_outputs):
        """Verify website_domain_name output is available."""
        assert www_common_outputs.get("website_domain_name"), (
            "website_domain_name output not found in www_common. "
            "Run terraform apply in src/www/common/"
        )

    def test_cloudfront_distribution_id_output_exists(self, www_common_outputs):
        """Verify cloudfront_distribution_id output is available."""
        assert www_common_outputs.get("cloudfront_distribution_id"), (
            "cloudfront_distribution_id output not found in www_common. "
            "Run terraform apply in src/www/common/"
        )


class TestCloudFrontDistribution:
    """Layer 3: Verify CloudFront distribution exists and is deployed."""

    def test_cloudfront_distribution_exists(self, cloudfront_client, www_common_outputs):
        """Verify the CloudFront distribution exists in AWS."""
        distribution_id = www_common_outputs.get("cloudfront_distribution_id")
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
                    "Run terraform apply in src/www/common/"
                )
            raise

    def test_cloudfront_distribution_is_deployed(self, cloudfront_client, www_common_outputs):
        """Verify the CloudFront distribution is deployed."""
        distribution_id = www_common_outputs.get("cloudfront_distribution_id")
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
