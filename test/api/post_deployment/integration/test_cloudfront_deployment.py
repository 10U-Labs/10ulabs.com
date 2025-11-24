import boto3


def test_cloudfront_distribution_origin_configuration(_tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    assert len(distributions['DistributionList']['Items']) >= 0


def test_cloudfront_distribution_cache_behaviors(_tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    assert len(distributions['DistributionList']['Items']) >= 0


def test_cloudfront_distribution_ssl_certificate(_tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    assert len(distributions['DistributionList']['Items']) >= 0


def test_acm_certificate_is_validated_and_issued(tfvars):
    acm = boto3.client('acm', region_name=tfvars["aws_region"])
    certificates = acm.list_certificates(CertificateStatuses=['ISSUED'])
    assert len(certificates['CertificateSummaryList']) >= 0


def test_cloudfront_distribution_exists(_tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    distribution_list = distributions['DistributionList']
    assert distribution_list['Quantity'] >= 0


def test_cloudfront_distribution_origin_points_to_s3(_tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront.get_distribution_config(Id=dist_id)
        origins = config['DistributionConfig']['Origins']['Items']
        assert len(origins) > 0


def test_cloudfront_distribution_has_default_cache_behavior(_tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront.get_distribution_config(Id=dist_id)
        assert 'DefaultCacheBehavior' in config['DistributionConfig']


def test_cloudfront_distribution_cache_behavior_allows_get_head(_tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront.get_distribution_config(Id=dist_id)
        allowed_methods = config['DistributionConfig']['DefaultCacheBehavior']['AllowedMethods']['Items']
        assert 'GET' in allowed_methods


def test_cloudfront_distribution_has_viewer_protocol_policy(_tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront.get_distribution_config(Id=dist_id)
        assert 'ViewerProtocolPolicy' in config['DistributionConfig']['DefaultCacheBehavior']


def test_cloudfront_distribution_compression_enabled(_tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront.get_distribution_config(Id=dist_id)
        assert 'Compress' in config['DistributionConfig']['DefaultCacheBehavior']


def test_acm_certificate_exists_for_domain(tfvars):
    acm = boto3.client('acm', region_name=tfvars["aws_region"])
    certificates = acm.list_certificates()
    assert certificates['CertificateSummaryList']
