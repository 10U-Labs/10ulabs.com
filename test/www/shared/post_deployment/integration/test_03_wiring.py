"""Layer 3: Wiring tests for www_shared post-deployment validation.

Verify components are connected properly. Assumes configuration tests passed.
"""
import pytest

pytestmark = pytest.mark.layer(3)


@pytest.fixture(name="cloudfront_origins", scope="module")
def cloudfront_origins_fixture(distribution_config):
    """Extract CloudFront origins from distribution config."""
    return distribution_config["DistributionConfig"]["Origins"]["Items"]


@pytest.fixture(name="viewer_certificate", scope="module")
def viewer_certificate_fixture(distribution_config):
    """Extract viewer certificate from distribution config."""
    return distribution_config["DistributionConfig"]["ViewerCertificate"]


@pytest.fixture(name="website_dns_record", scope="module")
def website_dns_record_fixture(route53_client, config):
    """Get the DNS A record for the website."""
    hosted_zone_id = config["hosted_zone_id"]
    website_fqdn = config["website_fqdn"]
    response = route53_client.list_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        StartRecordName=website_fqdn,
        StartRecordType="A",
        MaxItems="1"
    )
    records = response.get("ResourceRecordSets", [])
    matching = [r for r in records if r["Name"].rstrip(".") == website_fqdn]
    return matching[0] if matching else None


def test_cloudfront_origin_is_s3_bucket(cloudfront_origins, config):
    """Verify CloudFront origin points to the website S3 bucket."""
    bucket_name = config["website_bucket_name"]
    origin_domains = [o["DomainName"] for o in cloudfront_origins]
    matching = [d for d in origin_domains if bucket_name in d]
    assert matching, f"No origin found for bucket {bucket_name}. Origins: {origin_domains}"


def test_cloudfront_has_acm_certificate(viewer_certificate):
    """Verify CloudFront has an ACM certificate configured."""
    assert "ACMCertificateArn" in viewer_certificate, "CloudFront not using ACM certificate"


def test_cloudfront_acm_certificate_arn_format(viewer_certificate):
    """Verify CloudFront ACM certificate ARN has correct format."""
    arn = viewer_certificate.get("ACMCertificateArn", "")
    assert arn.startswith("arn:aws:acm:"), f"Invalid ACM ARN format: {arn}"


def test_route53_has_website_record(website_dns_record, config):
    """Verify Route53 has an A record for the website."""
    assert website_dns_record is not None, f"No A record found for {config['website_fqdn']}"


def test_route53_website_record_is_alias(website_dns_record, config):
    """Verify Route53 website record is an alias."""
    assert "AliasTarget" in website_dns_record, (
        f"Record for {config['website_fqdn']} is not an alias"
    )


def test_route53_alias_target_is_cloudfront(website_dns_record):
    """Verify Route53 alias target points to CloudFront."""
    alias_target = website_dns_record["AliasTarget"]["DNSName"]
    assert "cloudfront.net" in alias_target, (
        f"Alias does not point to CloudFront: {alias_target}"
    )
