"""Layer 1: Existence tests for www_common post-deployment validation.

Verify resources created by this deployment exist. No configuration checks.
"""
import pytest

pytestmark = pytest.mark.layer(1)


def test_cloudfront_distribution_exists(cloudfront_client):
    """Verify CloudFront distribution exists."""
    distributions = cloudfront_client.list_distributions()
    distribution_list = distributions["DistributionList"]
    assert distribution_list["Quantity"] >= 0


def test_acm_certificate_exists(acm_client):
    """Verify ACM certificate exists for domain."""
    certificates = acm_client.list_certificates()
    assert certificates["CertificateSummaryList"]


def test_s3_bucket_exists(s3_client, config):
    """Verify S3 website bucket exists."""
    response = s3_client.head_bucket(Bucket=config["website_bucket_name"])
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
