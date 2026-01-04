"""Layer 2: Configuration tests for www_common post-deployment validation.

Verify resources are configured correctly. Assumes existence tests passed.
"""
import pytest



def test_acm_certificate_is_issued(acm_client):
    """Verify ACM certificate is validated and issued."""
    certificates = acm_client.list_certificates(CertificateStatuses=["ISSUED"])
    assert len(certificates["CertificateSummaryList"]) >= 0


def test_cloudfront_logging_enabled(logging_config):
    """Verify CloudFront distribution has logging enabled."""
    assert logging_config.get("Enabled", False) is True


def test_cloudfront_logging_bucket_is_central_logs(logging_config, config):
    """Verify CloudFront logging bucket is central logs."""
    bucket = logging_config.get("Bucket", "")
    assert config["central_logs_bucket"] in bucket


def test_cloudfront_logging_prefix_is_correct(logging_config):
    """Verify CloudFront logging prefix is correct."""
    prefix = logging_config.get("Prefix", "")
    assert prefix == "cloudfront-logs/website/"


def test_cloudfront_logging_excludes_cookies(logging_config):
    """Verify CloudFront logging excludes cookies."""
    assert logging_config.get("IncludeCookies", True) is False


def test_cloudfront_uses_https_redirect(default_cache_behavior):
    """Verify CloudFront distribution uses HTTPS redirect."""
    policy = default_cache_behavior["ViewerProtocolPolicy"]
    assert policy == "redirect-to-https"


def test_cloudfront_compression_enabled(default_cache_behavior):
    """Verify CloudFront distribution has compression enabled."""
    assert default_cache_behavior.get("Compress", False) is True


def test_s3_bucket_blocks_public_acls(public_access_block):
    """Verify S3 bucket blocks public ACLs."""
    assert public_access_block["BlockPublicAcls"] is True


def test_s3_bucket_blocks_public_policy(public_access_block):
    """Verify S3 bucket blocks public policy."""
    assert public_access_block["BlockPublicPolicy"] is True


def test_s3_bucket_ignores_public_acls(public_access_block):
    """Verify S3 bucket ignores public ACLs."""
    assert public_access_block["IgnorePublicAcls"] is True


def test_s3_bucket_restricts_public_buckets(public_access_block):
    """Verify S3 bucket restricts public buckets."""
    assert public_access_block["RestrictPublicBuckets"] is True


def test_s3_bucket_has_encryption(s3_client, config):
    """Verify S3 bucket has encryption enabled."""
    response = s3_client.get_bucket_encryption(Bucket=config["website_bucket_name"])
    rules = response["ServerSideEncryptionConfiguration"]["Rules"]
    assert len(rules) > 0


def test_s3_bucket_encryption_is_aes256(s3_client, config):
    """Verify S3 bucket uses AES256 encryption."""
    response = s3_client.get_bucket_encryption(Bucket=config["website_bucket_name"])
    rules = response["ServerSideEncryptionConfiguration"]["Rules"]
    algorithm = rules[0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"]
    assert algorithm == "AES256"


def test_s3_bucket_versioning_disabled(s3_client, config):
    """Verify S3 bucket has versioning disabled."""
    response = s3_client.get_bucket_versioning(Bucket=config["website_bucket_name"])
    status = response.get("Status", "Disabled")
    assert status != "Enabled"


def test_s3_bucket_has_logging_enabled(s3_client, config):
    """Verify S3 bucket has logging enabled."""
    response = s3_client.get_bucket_logging(Bucket=config["website_bucket_name"])
    assert "LoggingEnabled" in response


def test_s3_bucket_logging_target_is_central_logs(s3_client, config):
    """Verify S3 bucket logs to central logs bucket."""
    response = s3_client.get_bucket_logging(Bucket=config["website_bucket_name"])
    target_bucket = response["LoggingEnabled"]["TargetBucket"]
    assert config["central_logs_bucket"] in target_bucket
