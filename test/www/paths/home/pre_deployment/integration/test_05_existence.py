"""Layer 5: Existence tests for www home page deployment prerequisites.

Test that prerequisite resources exist. Assumes authorization passed.
"""
import pytest

from test_fixtures.integration import create_www_common_s3_existence_tests


# Use common S3 bucket existence tests
TestWWWCommonS3 = create_www_common_s3_existence_tests()


class TestCloudFrontDistributionExists:
    """Layer 5: Verify CloudFront distribution exists."""

    def test_cloudfront_distribution_exists(
        self, cloudfront_distribution, www_common_outputs
    ):
        """Verify the CloudFront distribution exists in AWS."""
        distribution_id = www_common_outputs.get("cloudfront_distribution_id")
        if not distribution_id:
            pytest.skip("cloudfront_distribution_id output not available")
        if cloudfront_distribution is None:
            pytest.fail(
                f"CloudFront distribution '{distribution_id}' does not exist. "
                "Run terraform apply in src/www/common/"
            )
        dist_id_matches = cloudfront_distribution["Id"] == distribution_id
        assert dist_id_matches, (
            f"Distribution ID mismatch: expected {distribution_id}"
        )

    def test_cloudfront_distribution_has_id(
        self, cloudfront_distribution
    ):
        """Verify the CloudFront distribution has an ID."""
        if cloudfront_distribution is None:
            pytest.skip("cloudfront_distribution not available")
        has_id = "Id" in cloudfront_distribution
        assert has_id, "CloudFront distribution should have an Id"


class TestTerraformOutputsExist:
    """Layer 5: Verify terraform outputs contain expected values."""

    def test_website_domain_name_output_exists(self, www_common_outputs):
        """Verify website_domain_name output is available."""
        domain_name = www_common_outputs.get("website_domain_name")
        has_domain_name = domain_name is not None and len(domain_name) > 0
        assert has_domain_name, (
            "website_domain_name output not found in www_common. "
            "Run terraform apply in src/www/common/"
        )

    def test_cloudfront_distribution_id_output_exists(self, www_common_outputs):
        """Verify cloudfront_distribution_id output is available."""
        distribution_id = www_common_outputs.get("cloudfront_distribution_id")
        has_distribution_id = distribution_id is not None and len(distribution_id) > 0
        assert has_distribution_id, (
            "cloudfront_distribution_id output not found in www_common. "
            "Run terraform apply in src/www/common/"
        )
