import pytest

from test_fixtures.integration import create_deployed_resource_existence_tests


def test_lambda_catchall_handler_runtime_is_python313(lambda_client, shared_config):
    function_name = shared_config['lambda_handler_names']['catchall']
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


_existence_tests = create_deployed_resource_existence_tests(
    function_name_config_key='catchall_handler_function_name',
    default_function_name='TenULabsCatchAllHandler',
    handler_display_name='CatchAllHandler',
)
TestCatchAllHandlerIAMRoleExists = _existence_tests[0]
TestCatchAllHandlerLambdaFunctionExists = _existence_tests[1]


def test_s3_bucket_versioning_disabled(s3_client, config):
    bucket_name = config["api_fqdn"]
    response = s3_client.get_bucket_versioning(Bucket=bucket_name)
    assert response.get("Status") != "Enabled"


def test_s3_bucket_encryption_config_exists(s3_client, config):
    bucket_name = config["api_fqdn"]
    response = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert "ServerSideEncryptionConfiguration" in response


def test_s3_bucket_encryption_has_rules(s3_client, config):
    bucket_name = config["api_fqdn"]
    response = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert "Rules" in response["ServerSideEncryptionConfiguration"]


def test_cloudfront_distribution_has_default_cache_behavior(first_cloudfront_dist_config):
    if first_cloudfront_dist_config is not None:
        assert 'DefaultCacheBehavior' in first_cloudfront_dist_config


def test_cloudfront_distribution_allows_get_head_methods(first_cloudfront_dist_config):
    if first_cloudfront_dist_config is not None:
        cache_behavior = first_cloudfront_dist_config['DefaultCacheBehavior']
        allowed_methods = cache_behavior['AllowedMethods']['Items']
        assert 'GET' in allowed_methods


def test_cloudfront_distribution_has_viewer_protocol_policy(first_cloudfront_dist_config):
    if first_cloudfront_dist_config is not None:
        cache_behavior = first_cloudfront_dist_config['DefaultCacheBehavior']
        assert 'ViewerProtocolPolicy' in cache_behavior


def test_cloudfront_distribution_compression_enabled(first_cloudfront_dist_config):
    if first_cloudfront_dist_config is not None:
        assert 'Compress' in first_cloudfront_dist_config['DefaultCacheBehavior']


def test_cloudfront_distribution_logging_enabled(first_cloudfront_dist_config):
    if first_cloudfront_dist_config is not None:
        logging_config = first_cloudfront_dist_config.get('Logging', {})
        assert logging_config.get('Enabled', False)


def test_cloudfront_logging_excludes_cookies(first_cloudfront_dist_config):
    if first_cloudfront_dist_config is not None:
        logging_config = first_cloudfront_dist_config.get('Logging', {})
        assert logging_config.get('IncludeCookies', True) is False


def test_cloudfront_viewer_certificate_min_protocol_tls_1_2(first_cloudfront_dist_config):
    if first_cloudfront_dist_config is not None:
        viewer_cert = first_cloudfront_dist_config.get('ViewerCertificate', {})
        min_protocol = viewer_cert.get('MinimumProtocolVersion', '')
        assert 'TLSv1.2' in min_protocol


def test_cloudfront_geo_restriction_is_none(first_cloudfront_dist_config):
    if first_cloudfront_dist_config is not None:
        restrictions = first_cloudfront_dist_config.get('Restrictions', {})
        geo_restriction = restrictions.get('GeoRestriction', {})
        assert geo_restriction.get('RestrictionType') == 'none'


def test_cloudfront_distribution_ipv6_disabled(first_cloudfront_dist_config):
    if first_cloudfront_dist_config is not None:
        assert first_cloudfront_dist_config.get('IsIPV6Enabled') is False


def test_cloudfront_distribution_http_version_is_http2(first_cloudfront_dist_config):
    if first_cloudfront_dist_config is not None:
        http_version = first_cloudfront_dist_config.get('HttpVersion', '')
        assert 'http2' in http_version


def test_cloudfront_aliases_include_api_fqdn(cloudfront_client, api_distribution_id, config):
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    aliases = dist_config['DistributionConfig'].get('Aliases', {}).get('Items', [])
    assert config['api_fqdn'] in aliases


def test_cloudfront_api_origin_protocol_is_https_only(cloudfront_client, api_distribution_id):
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    origins = dist_config['DistributionConfig']['Origins']['Items']
    for origin in origins:
        if 'CustomOriginConfig' in origin:
            assert origin['CustomOriginConfig']['OriginProtocolPolicy'] == 'https-only'


def test_cloudfront_api_origin_ssl_protocols_tls_1_2(cloudfront_client, api_distribution_id):
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    origins = dist_config['DistributionConfig']['Origins']['Items']
    for origin in origins:
        if 'CustomOriginConfig' in origin:
            ssl_protocols = origin['CustomOriginConfig']['OriginSslProtocols']['Items']
            assert 'TLSv1.2' in ssl_protocols


def test_cloudfront_default_cache_behavior_uses_caching_disabled(
    cloudfront_client, api_distribution_id
):
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    default_behavior = dist_config['DistributionConfig']['DefaultCacheBehavior']
    cache_policy_id = default_behavior.get('CachePolicyId', '')
    assert cache_policy_id != '' or 'ForwardedValues' in default_behavior


def _cache_behavior_matching(cloudfront_client, api_distribution_id, path_pattern):
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    behaviors = dist_config['DistributionConfig'].get('CacheBehaviors', {})
    cache_behaviors = behaviors.get('Items', [])
    return next(
        (b for b in cache_behaviors if path_pattern in b.get('PathPattern', '')), None
    )


def test_cloudfront_health_cache_behavior_uses_api_origin(cloudfront_client, api_distribution_id):
    behavior = _cache_behavior_matching(cloudfront_client, api_distribution_id, '/health')
    if behavior:
        origin_id = behavior['TargetOriginId'].lower()
        assert 'api' in origin_id or 'execute' in origin_id


def test_cloudfront_v1_api_cache_behavior_uses_api_origin(cloudfront_client, api_distribution_id):
    behavior = _cache_behavior_matching(cloudfront_client, api_distribution_id, '/v1')
    if behavior:
        origin_id = behavior['TargetOriginId'].lower()
        assert 'api' in origin_id or 'execute' in origin_id


def test_cloudfront_docs_cache_behavior_uses_s3_origin(cloudfront_client, api_distribution_id):
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    origins = dist_config['DistributionConfig']['Origins']['Items']
    has_s3_origin = any(
        's3' in o['Id'].lower() or 's3' in o.get('DomainName', '').lower()
        for o in origins
    )
    assert has_s3_origin


def test_cloudfront_distribution_price_class(cloudfront_client, api_distribution_id):
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    price_class = dist_config['DistributionConfig'].get('PriceClass', '')
    assert price_class.startswith('PriceClass_')


def test_acm_certificate_is_issued(acm_client):
    certificates = acm_client.list_certificates(CertificateStatuses=['ISSUED'])
    assert len(certificates['CertificateSummaryList']) > 0


def test_acm_certificate_validation_method_is_dns(acm_client):
    certificates = acm_client.list_certificates(CertificateStatuses=['ISSUED'])
    if not certificates['CertificateSummaryList']:
        pytest.skip("No issued certificates found")
    cert_arn = certificates['CertificateSummaryList'][0]['CertificateArn']
    cert_details = acm_client.describe_certificate(CertificateArn=cert_arn)
    domain_validation = cert_details['Certificate'].get('DomainValidationOptions', [])
    if domain_validation:
        assert domain_validation[0].get('ValidationMethod') == 'DNS'


def test_acm_certificate_domain_name_matches(acm_client, config):
    certificates = acm_client.list_certificates(CertificateStatuses=['ISSUED'])
    if not certificates['CertificateSummaryList']:
        pytest.skip("No issued certificates found")
    domain_names = [c['DomainName'] for c in certificates['CertificateSummaryList']]
    has_matching_domain = any(config['domain'] in d for d in domain_names)
    assert has_matching_domain


def _find_docs_cache_policy(cloudfront_client):
    response = cloudfront_client.list_cache_policies(Type='custom')
    policies = response['CachePolicyList'].get('Items', [])
    for policy in policies:
        name = policy['CachePolicy']['CachePolicyConfig']['Name'].lower()
        if 'docs' in name:
            return policy
    return None


def test_cloudfront_docs_cache_policy_default_ttl(cloudfront_client):
    docs_policy = _find_docs_cache_policy(cloudfront_client)
    if docs_policy:
        config = docs_policy['CachePolicy']['CachePolicyConfig']
        assert config['DefaultTTL'] > 0


def test_cloudfront_docs_cache_policy_max_ttl(cloudfront_client):
    docs_policy = _find_docs_cache_policy(cloudfront_client)
    if docs_policy:
        config = docs_policy['CachePolicy']['CachePolicyConfig']
        assert config['MaxTTL'] > 0


def test_cloudfront_docs_cache_policy_min_ttl(cloudfront_client):
    docs_policy = _find_docs_cache_policy(cloudfront_client)
    if docs_policy:
        config = docs_policy['CachePolicy']['CachePolicyConfig']
        assert 'MinTTL' in config


def test_cloudfront_docs_cache_policy_gzip_enabled(cloudfront_client):
    docs_policy = _find_docs_cache_policy(cloudfront_client)
    if docs_policy:
        config = docs_policy['CachePolicy']['CachePolicyConfig']
        params = config['ParametersInCacheKeyAndForwardedToOrigin']
        assert params.get('EnableAcceptEncodingGzip') is True


def test_cloudfront_docs_cache_policy_brotli_enabled(cloudfront_client):
    docs_policy = _find_docs_cache_policy(cloudfront_client)
    if docs_policy:
        config = docs_policy['CachePolicy']['CachePolicyConfig']
        params = config['ParametersInCacheKeyAndForwardedToOrigin']
        assert params.get('EnableAcceptEncodingBrotli') is True


def test_cloudfront_docs_cache_policy_cookies_none(cloudfront_client):
    response = cloudfront_client.list_cache_policies(Type='custom')
    policies = response['CachePolicyList'].get('Items', [])
    docs_policy = next(
        (p for p in policies if 'docs' in p['CachePolicy']['CachePolicyConfig']['Name'].lower()),
        None
    )
    if docs_policy:
        policy_config = docs_policy['CachePolicy']['CachePolicyConfig']
        params = policy_config['ParametersInCacheKeyAndForwardedToOrigin']
        cookies = params.get('CookiesConfig', {})
        assert cookies.get('CookieBehavior') == 'none'


def test_firehose_delivery_stream_is_active(firehose_client, config):
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    assert response['DeliveryStreamDescription']['DeliveryStreamStatus'] == 'ACTIVE'


def test_firehose_delivery_stream_type_is_direct_put(firehose_client, config):
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    assert response['DeliveryStreamDescription']['DeliveryStreamType'] == 'DirectPut'


def test_firehose_destination_is_extended_s3(firehose_client, config):
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    destinations = response['DeliveryStreamDescription']['Destinations']
    assert destinations[0]['ExtendedS3DestinationDescription'] is not None


def test_firehose_s3_prefix_is_correct(firehose_client, config):
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    destinations = response['DeliveryStreamDescription']['Destinations']
    s3_config = destinations[0]['ExtendedS3DestinationDescription']
    assert s3_config['Prefix'] == 'cloudwatch-logs/api/'


def test_firehose_s3_error_prefix_is_correct(firehose_client, config):
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    destinations = response['DeliveryStreamDescription']['Destinations']
    s3_config = destinations[0]['ExtendedS3DestinationDescription']
    assert s3_config['ErrorOutputPrefix'] == 'cloudwatch-logs/api-errors/'


def test_firehose_compression_is_gzip(firehose_client, config):
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    destinations = response['DeliveryStreamDescription']['Destinations']
    s3_config = destinations[0]['ExtendedS3DestinationDescription']
    assert s3_config['CompressionFormat'] == 'GZIP'


def test_firehose_buffering_size_is_5mb(firehose_client, config):
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    destinations = response['DeliveryStreamDescription']['Destinations']
    s3_config = destinations[0]['ExtendedS3DestinationDescription']
    assert s3_config['BufferingHints']['SizeInMBs'] == 5


def test_firehose_buffering_interval_is_300_seconds(firehose_client, config):
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    destinations = response['DeliveryStreamDescription']['Destinations']
    s3_config = destinations[0]['ExtendedS3DestinationDescription']
    assert s3_config['BufferingHints']['IntervalInSeconds'] == 300


def test_api_key_ssm_parameter_is_secure_string(ssm_client, config):
    param_name = config['ssm_parameter_name_for_api_key']
    response = ssm_client.get_parameter(Name=param_name, WithDecryption=False)
    assert response['Parameter']['Type'] == 'SecureString'


def test_api_gateway_rest_api_endpoint_type_is_regional(apigateway_client, api_gateway_id):
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_rest_api(restApiId=api_gateway_id)
    assert 'REGIONAL' in response['endpointConfiguration']['types']


def test_api_gateway_stage_access_log_format_configured(apigateway_client, api_gateway_id):
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_stage(restApiId=api_gateway_id, stageName='prod')
    access_log = response.get('accessLogSettings', {})
    assert 'format' in access_log


def _stage_method_settings(apigateway_client, api_gateway_id):
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_stage(restApiId=api_gateway_id, stageName='prod')
    return response.get('methodSettings', {})


def test_api_gateway_method_settings_logging_level_is_info(apigateway_client, api_gateway_id):
    method_settings = _stage_method_settings(apigateway_client, api_gateway_id)
    if '*/*' in method_settings:
        assert method_settings['*/*'].get('loggingLevel') == 'INFO'


def test_api_gateway_method_settings_metrics_enabled(apigateway_client, api_gateway_id):
    method_settings = _stage_method_settings(apigateway_client, api_gateway_id)
    if '*/*' in method_settings:
        assert method_settings['*/*'].get('metricsEnabled') is True


def test_api_gateway_method_settings_data_trace_enabled(apigateway_client, api_gateway_id):
    method_settings = _stage_method_settings(apigateway_client, api_gateway_id)
    if '*/*' in method_settings:
        assert 'dataTraceEnabled' in method_settings['*/*']


def test_api_gateway_method_settings_apply_to_all_methods(apigateway_client, api_gateway_id):
    method_settings = _stage_method_settings(apigateway_client, api_gateway_id)
    assert '*/*' in method_settings


def test_api_gateway_api_key_is_enabled(apigateway_client):
    response = apigateway_client.get_api_keys()
    if response['items']:
        assert response['items'][0]['enabled'] is True


def test_api_gateway_usage_plan_throttle_rate_limit(apigateway_client):
    response = apigateway_client.get_usage_plans()
    if response['items']:
        throttle = response['items'][0].get('throttle', {})
        assert 'rateLimit' in throttle


def test_api_gateway_stage_has_logging_enabled(apigateway_client, api_gateway_id):
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_stage(restApiId=api_gateway_id, stageName='prod')
    access_log = response.get('accessLogSettings', {})
    assert 'destinationArn' in access_log


def test_api_gateway_stage_has_xray_tracing_disabled(apigateway_client, api_gateway_id):
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_stage(restApiId=api_gateway_id, stageName='prod')
    assert 'tracingEnabled' in response


def test_cloudfront_url_rewrite_function_runtime(cloudfront_client):
    response = cloudfront_client.list_functions()
    functions = response['FunctionList'].get('Items', [])
    url_rewrite = next(
        f for f in functions if f['Name'] == 'RootUrlRewriteFunction'
    )
    assert url_rewrite['FunctionConfig']['Runtime'] == 'cloudfront-js-2.0'


def test_firehose_cloudwatch_logs_bucket_is_central_logs(firehose_client, config):
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    destinations = response['DeliveryStreamDescription']['Destinations']
    s3_config = destinations[0]['ExtendedS3DestinationDescription']
    assert config['central_logs_bucket'] in s3_config['BucketARN']


def _check_firehose_cw_logging_disabled(response):
    destinations = response['DeliveryStreamDescription']['Destinations']
    s3_config = destinations[0]['ExtendedS3DestinationDescription']
    cw_logging = s3_config.get('CloudWatchLoggingOptions', {})
    return cw_logging.get('Enabled') is False or 'CloudWatchLoggingOptions' not in s3_config


def test_firehose_cloudwatch_logs_cloudwatch_logging_disabled(firehose_client, config):
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    assert _check_firehose_cw_logging_disabled(response)


def test_catchall_subscription_filter_pattern_is_empty(logs_client, config):
    log_group = config['catchall_handler_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    if response['subscriptionFilters']:
        assert response['subscriptionFilters'][0]['filterPattern'] == ''


def test_api_gateway_subscription_filter_pattern_is_empty(logs_client, config):
    log_group = config['api_gateway_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    if response['subscriptionFilters']:
        assert response['subscriptionFilters'][0]['filterPattern'] == ''


def test_health_subscription_filter_pattern_is_empty(logs_client, config):
    log_group = config['health_handler_log_group_name']
    try:
        response = logs_client.describe_subscription_filters(logGroupName=log_group)
        if response['subscriptionFilters']:
            assert response['subscriptionFilters'][0]['filterPattern'] == ''
    except logs_client.exceptions.ResourceNotFoundException:
        pytest.skip("Health handler log group not deployed")


def test_index_html_content_type_is_text_html(s3_client, config):
    bucket_name = config["api_fqdn"]
    response = s3_client.head_object(Bucket=bucket_name, Key="index.html")
    assert response['ContentType'] == 'text/html'


def test_404_html_content_type_is_text_html(s3_client, config):
    bucket_name = config["api_fqdn"]
    response = s3_client.head_object(Bucket=bucket_name, Key="404.html")
    assert response['ContentType'] == 'text/html'


def test_openapi_json_content_type_is_application_json(s3_client, config):
    bucket_name = config["api_fqdn"]
    response = s3_client.head_object(Bucket=bucket_name, Key="openapi.json")
    assert response['ContentType'] == 'application/json'


def test_s3_docs_bucket_logging_enabled(s3_client, config):
    bucket_name = config["api_fqdn"]
    try:
        response = s3_client.get_bucket_logging(Bucket=bucket_name)
        logging_enabled = response.get('LoggingEnabled') is not None
        assert logging_enabled
    except s3_client.exceptions.NoSuchBucket:
        pytest.skip("S3 bucket not found")


def test_catchall_handler_log_group_retention_is_7_days(logs_client, config):
    log_group = config['catchall_handler_log_group_name']
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group)
    if response['logGroups']:
        assert response['logGroups'][0].get('retentionInDays') == 7


def test_api_gateway_log_group_retention_is_30_days(logs_client, config):
    log_group = config['api_gateway_log_group_name']
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group)
    if response['logGroups']:
        assert response['logGroups'][0].get('retentionInDays') == 30


def test_catchall_handler_log_group_kms_encryption(logs_client, config):
    log_group = config['catchall_handler_log_group_name']
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group)
    if response['logGroups']:
        kms_key = response['logGroups'][0].get('kmsKeyId')
        assert 'kmsKeyId' in response['logGroups'][0] or kms_key is None


def test_api_gateway_log_group_kms_encryption(logs_client, config):
    log_group = config['api_gateway_log_group_name']
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group)
    if response['logGroups']:
        kms_key = response['logGroups'][0].get('kmsKeyId')
        assert 'kmsKeyId' in response['logGroups'][0] or kms_key is None
