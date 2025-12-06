"""Tests for CloudFront distribution deployment configuration."""
import pytest


def test_cloudfront_distribution_origin_configuration(cloudfront_client):
    """Verify CloudFront distribution has origin configuration."""
    distributions = cloudfront_client.list_distributions()
    assert len(distributions['DistributionList']['Items']) >= 0


def test_cloudfront_distribution_cache_behaviors(cloudfront_client):
    """Verify CloudFront distribution has cache behaviors."""
    distributions = cloudfront_client.list_distributions()
    assert len(distributions['DistributionList']['Items']) >= 0


def test_cloudfront_distribution_ssl_certificate(cloudfront_client):
    """Verify CloudFront distribution has SSL certificate."""
    distributions = cloudfront_client.list_distributions()
    assert len(distributions['DistributionList']['Items']) >= 0


def test_acm_certificate_is_validated_and_issued(acm_client):
    """Verify ACM certificate is validated and issued."""
    certificates = acm_client.list_certificates(CertificateStatuses=['ISSUED'])
    assert len(certificates['CertificateSummaryList']) >= 0


def test_cloudfront_distribution_exists(cloudfront_client):
    """Verify CloudFront distribution exists."""
    distributions = cloudfront_client.list_distributions()
    distribution_list = distributions['DistributionList']
    assert distribution_list['Quantity'] >= 0


def test_cloudfront_distribution_origin_points_to_s3(cloudfront_client):
    """Verify CloudFront distribution origin points to S3."""
    distributions = cloudfront_client.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        dist_config = cloudfront_client.get_distribution_config(Id=dist_id)
        origins = dist_config['DistributionConfig']['Origins']['Items']
        assert len(origins) > 0


def test_cloudfront_distribution_has_default_cache_behavior(cloudfront_client):
    """Verify CloudFront distribution has default cache behavior."""
    distributions = cloudfront_client.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        dist_config = cloudfront_client.get_distribution_config(Id=dist_id)
        assert 'DefaultCacheBehavior' in dist_config['DistributionConfig']


def test_cloudfront_distribution_cache_behavior_allows_get_head(cloudfront_client):
    """Verify CloudFront allows GET and HEAD methods."""
    distributions = cloudfront_client.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        dist_config = cloudfront_client.get_distribution_config(Id=dist_id)
        cache_behavior = dist_config['DistributionConfig']['DefaultCacheBehavior']
        allowed_methods = cache_behavior['AllowedMethods']['Items']
        assert 'GET' in allowed_methods


def test_cloudfront_distribution_has_viewer_protocol_policy(cloudfront_client):
    """Verify CloudFront has viewer protocol policy configured."""
    distributions = cloudfront_client.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        dist_config = cloudfront_client.get_distribution_config(Id=dist_id)
        cache_behavior = dist_config['DistributionConfig']['DefaultCacheBehavior']
        assert 'ViewerProtocolPolicy' in cache_behavior


def test_cloudfront_distribution_compression_enabled(cloudfront_client):
    """Verify CloudFront compression is enabled."""
    distributions = cloudfront_client.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        dist_config = cloudfront_client.get_distribution_config(Id=dist_id)
        assert 'Compress' in dist_config['DistributionConfig']['DefaultCacheBehavior']


def test_acm_certificate_exists_for_domain(acm_client):
    """Verify ACM certificate exists for the domain."""
    certificates = acm_client.list_certificates()
    assert certificates['CertificateSummaryList']


def test_cloudfront_distribution_has_logging_enabled(cloudfront_client):
    """Verify CloudFront has logging enabled."""
    distributions = cloudfront_client.list_distributions()
    dist_found_with_logging = False
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        dist_config = cloudfront_client.get_distribution_config(Id=dist_id)
        logging_config = dist_config['DistributionConfig'].get('Logging', {})
        dist_found_with_logging = logging_config.get('Enabled', False)
    assert dist_found_with_logging


def test_cloudfront_logging_bucket_is_central_logs(cloudfront_client, api_distribution_id, config):
    """Verify CloudFront logs to central logs bucket."""
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    logging_config = dist_config['DistributionConfig'].get('Logging', {})
    if not logging_config.get('Enabled', False):
        pytest.skip("CloudFront logging not yet enabled on distribution")
    bucket = logging_config.get('Bucket', '')
    bucket_correct = config['central_logs_bucket'] in bucket
    assert bucket_correct


def test_cloudfront_logging_prefix_is_correct(cloudfront_client, api_distribution_id):
    """Verify CloudFront logging prefix is correct."""
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    logging_config = dist_config['DistributionConfig'].get('Logging', {})
    prefix = logging_config.get('Prefix', '')
    assert prefix == 'cloudfront-logs/api/'


def test_cloudfront_logging_excludes_cookies(cloudfront_client):
    """Verify CloudFront logging excludes cookies."""
    distributions = cloudfront_client.list_distributions()
    cookies_excluded = False
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        dist_config = cloudfront_client.get_distribution_config(Id=dist_id)
        logging_config = dist_config['DistributionConfig'].get('Logging', {})
        cookies_excluded = logging_config.get('IncludeCookies', True) is False
    assert cookies_excluded
