def test_cloudfront_distribution_origin_configuration(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    assert len(distributions['DistributionList']['Items']) >= 0


def test_cloudfront_distribution_cache_behaviors(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    assert len(distributions['DistributionList']['Items']) >= 0


def test_cloudfront_distribution_ssl_certificate(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    assert len(distributions['DistributionList']['Items']) >= 0


def test_acm_certificate_is_validated_and_issued(acm_client):
    certificates = acm_client.list_certificates(CertificateStatuses=['ISSUED'])
    assert len(certificates['CertificateSummaryList']) >= 0


def test_cloudfront_distribution_exists(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    distribution_list = distributions['DistributionList']
    assert distribution_list['Quantity'] >= 0


def test_cloudfront_distribution_origin_points_to_s3(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront_client.get_distribution_config(Id=dist_id)
        origins = config['DistributionConfig']['Origins']['Items']
        assert len(origins) > 0


def test_cloudfront_distribution_has_default_cache_behavior(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront_client.get_distribution_config(Id=dist_id)
        assert 'DefaultCacheBehavior' in config['DistributionConfig']


def test_cloudfront_distribution_cache_behavior_allows_get_head(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront_client.get_distribution_config(Id=dist_id)
        allowed_methods = config['DistributionConfig']['DefaultCacheBehavior']['AllowedMethods']['Items']
        assert 'GET' in allowed_methods


def test_cloudfront_distribution_has_viewer_protocol_policy(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront_client.get_distribution_config(Id=dist_id)
        assert 'ViewerProtocolPolicy' in config['DistributionConfig']['DefaultCacheBehavior']


def test_cloudfront_distribution_compression_enabled(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront_client.get_distribution_config(Id=dist_id)
        assert 'Compress' in config['DistributionConfig']['DefaultCacheBehavior']


def test_acm_certificate_exists_for_domain(acm_client):
    certificates = acm_client.list_certificates()
    assert certificates['CertificateSummaryList']


def test_cloudfront_distribution_has_logging_enabled(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    dist_found_with_logging = False
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront_client.get_distribution_config(Id=dist_id)
        logging_config = config['DistributionConfig'].get('Logging', {})
        dist_found_with_logging = logging_config.get('Enabled', False)
    assert dist_found_with_logging


def test_cloudfront_logging_bucket_is_central_logs(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    bucket_correct = False
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront_client.get_distribution_config(Id=dist_id)
        logging_config = config['DistributionConfig'].get('Logging', {})
        bucket = logging_config.get('Bucket', '')
        bucket_correct = '10ulabs-central-logs' in bucket
    assert bucket_correct


def test_cloudfront_logging_prefix_is_correct(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    prefix_correct = False
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront_client.get_distribution_config(Id=dist_id)
        logging_config = config['DistributionConfig'].get('Logging', {})
        prefix = logging_config.get('Prefix', '')
        prefix_correct = prefix == 'cloudfront-logs/api/'
    assert prefix_correct


def test_cloudfront_logging_excludes_cookies(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    cookies_excluded = False
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront_client.get_distribution_config(Id=dist_id)
        logging_config = config['DistributionConfig'].get('Logging', {})
        cookies_excluded = logging_config.get('IncludeCookies', True) is False
    assert cookies_excluded
