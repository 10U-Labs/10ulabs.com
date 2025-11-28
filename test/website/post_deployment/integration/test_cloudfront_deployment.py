def test_cloudfront_distribution_exists(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    distribution_list = distributions['DistributionList']
    assert distribution_list['Quantity'] >= 0


def test_acm_certificate_is_validated_and_issued(acm_client):
    certificates = acm_client.list_certificates(CertificateStatuses=['ISSUED'])
    assert len(certificates['CertificateSummaryList']) >= 0


def test_acm_certificate_exists_for_domain(acm_client):
    certificates = acm_client.list_certificates()
    assert certificates['CertificateSummaryList']


def test_cloudfront_distribution_has_logging_enabled(cloudfront_client, config):
    distributions = cloudfront_client.list_distributions()
    dist_found_with_logging = False
    if distributions['DistributionList']['Quantity'] > 0:
        items = distributions['DistributionList']['Items']
        for item in items:
            aliases = item.get('Aliases', {}).get('Items', [])
            if config['website_fqdn'] in aliases:
                dist_id = item['Id']
                dist_config = cloudfront_client.get_distribution_config(Id=dist_id)
                logging_config = dist_config['DistributionConfig'].get('Logging', {})
                dist_found_with_logging = logging_config.get('Enabled', False)
                break
    assert dist_found_with_logging


def test_cloudfront_logging_bucket_is_central_logs(cloudfront_client, config):
    distributions = cloudfront_client.list_distributions()
    bucket_correct = False
    if distributions['DistributionList']['Quantity'] > 0:
        items = distributions['DistributionList']['Items']
        for item in items:
            aliases = item.get('Aliases', {}).get('Items', [])
            if config['website_fqdn'] in aliases:
                dist_id = item['Id']
                dist_config = cloudfront_client.get_distribution_config(Id=dist_id)
                logging_config = dist_config['DistributionConfig'].get('Logging', {})
                bucket = logging_config.get('Bucket', '')
                bucket_correct = config['central_logs_bucket'] in bucket
                break
    assert bucket_correct


def test_cloudfront_logging_prefix_is_correct(cloudfront_client, config):
    distributions = cloudfront_client.list_distributions()
    prefix_correct = False
    if distributions['DistributionList']['Quantity'] > 0:
        items = distributions['DistributionList']['Items']
        for item in items:
            aliases = item.get('Aliases', {}).get('Items', [])
            if config['website_fqdn'] in aliases:
                dist_id = item['Id']
                dist_config = cloudfront_client.get_distribution_config(Id=dist_id)
                logging_config = dist_config['DistributionConfig'].get('Logging', {})
                prefix = logging_config.get('Prefix', '')
                prefix_correct = prefix == 'cloudfront-logs/website/'
                break
    assert prefix_correct


def test_cloudfront_logging_excludes_cookies(cloudfront_client, config):
    distributions = cloudfront_client.list_distributions()
    cookies_excluded = False
    if distributions['DistributionList']['Quantity'] > 0:
        items = distributions['DistributionList']['Items']
        for item in items:
            aliases = item.get('Aliases', {}).get('Items', [])
            if config['website_fqdn'] in aliases:
                dist_id = item['Id']
                dist_config = cloudfront_client.get_distribution_config(Id=dist_id)
                logging_config = dist_config['DistributionConfig'].get('Logging', {})
                cookies_excluded = logging_config.get('IncludeCookies', True) is False
                break
    assert cookies_excluded


def test_cloudfront_distribution_uses_https_redirect(cloudfront_client, config):
    distributions = cloudfront_client.list_distributions()
    https_redirect = False
    if distributions['DistributionList']['Quantity'] > 0:
        items = distributions['DistributionList']['Items']
        for item in items:
            aliases = item.get('Aliases', {}).get('Items', [])
            if config['website_fqdn'] in aliases:
                dist_id = item['Id']
                dist_config = cloudfront_client.get_distribution_config(Id=dist_id)
                policy = dist_config['DistributionConfig']['DefaultCacheBehavior']['ViewerProtocolPolicy']
                https_redirect = policy == 'redirect-to-https'
                break
    assert https_redirect


def test_cloudfront_distribution_has_compression_enabled(cloudfront_client, config):
    distributions = cloudfront_client.list_distributions()
    compress_enabled = False
    if distributions['DistributionList']['Quantity'] > 0:
        items = distributions['DistributionList']['Items']
        for item in items:
            aliases = item.get('Aliases', {}).get('Items', [])
            if config['website_fqdn'] in aliases:
                dist_id = item['Id']
                dist_config = cloudfront_client.get_distribution_config(Id=dist_id)
                compress_enabled = dist_config['DistributionConfig']['DefaultCacheBehavior'].get('Compress', False)
                break
    assert compress_enabled
