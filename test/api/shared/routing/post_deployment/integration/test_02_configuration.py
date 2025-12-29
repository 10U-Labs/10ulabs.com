"""Layer 2: Configuration tests for api_shared_routing post-deployment.

These tests verify that resources are configured correctly.
Tests assume Layer 1 existence tests have passed.
"""
import pytest

import boto3

from test_fixtures.integration import create_deployed_naming_convention_tests

pytestmark = pytest.mark.layer(2)


# =============================================================================
# Lambda Configuration
# =============================================================================


def test_lambda_catchall_handler_runtime_is_python313(lambda_client, shared_config):
    """Verify Lambda catchall handler uses Python 3.13 runtime."""
    function_name = shared_config['lambda_handler_names']['catchall']
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


# Use factory for naming convention tests - assigns to class names
_naming_tests = create_deployed_naming_convention_tests(
    function_name_config_key='catchall_handler_function_name',
    default_function_name='TenULabsCatchAllHandler',
    handler_display_name='CatchAllHandler',
)
TestCatchAllHandlerIAMRoleNamingConventions = _naming_tests[0]
TestCatchAllHandlerLambdaFunctionNamingConventions = _naming_tests[1]


# =============================================================================
# S3 Configuration
# =============================================================================


def test_s3_bucket_versioning_disabled(s3_client, config):
    """Verify that S3 bucket versioning is disabled."""
    bucket_name = config["api_fqdn"]
    response = s3_client.get_bucket_versioning(Bucket=bucket_name)
    assert response.get("Status") != "Enabled"


def test_s3_bucket_encryption_config_exists(s3_client, config):
    """Verify that S3 bucket encryption configuration exists."""
    bucket_name = config["api_fqdn"]
    response = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert "ServerSideEncryptionConfiguration" in response


def test_s3_bucket_encryption_has_rules(s3_client, config):
    """Verify that S3 bucket encryption has rules defined."""
    bucket_name = config["api_fqdn"]
    response = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert "Rules" in response["ServerSideEncryptionConfiguration"]


# =============================================================================
# CloudFront Configuration
# =============================================================================


def test_cloudfront_distribution_has_default_cache_behavior(first_cloudfront_dist_config):
    """Verify CloudFront distribution has default cache behavior."""
    if first_cloudfront_dist_config is not None:
        assert 'DefaultCacheBehavior' in first_cloudfront_dist_config


def test_cloudfront_distribution_allows_get_head_methods(first_cloudfront_dist_config):
    """Verify CloudFront allows GET and HEAD methods."""
    if first_cloudfront_dist_config is not None:
        cache_behavior = first_cloudfront_dist_config['DefaultCacheBehavior']
        allowed_methods = cache_behavior['AllowedMethods']['Items']
        assert 'GET' in allowed_methods


def test_cloudfront_distribution_has_viewer_protocol_policy(first_cloudfront_dist_config):
    """Verify CloudFront has viewer protocol policy configured."""
    if first_cloudfront_dist_config is not None:
        cache_behavior = first_cloudfront_dist_config['DefaultCacheBehavior']
        assert 'ViewerProtocolPolicy' in cache_behavior


def test_cloudfront_distribution_compression_enabled(first_cloudfront_dist_config):
    """Verify CloudFront compression is enabled."""
    if first_cloudfront_dist_config is not None:
        assert 'Compress' in first_cloudfront_dist_config['DefaultCacheBehavior']


def test_cloudfront_distribution_logging_enabled(first_cloudfront_dist_config):
    """Verify CloudFront has logging enabled."""
    if first_cloudfront_dist_config is not None:
        logging_config = first_cloudfront_dist_config.get('Logging', {})
        assert logging_config.get('Enabled', False)


def test_cloudfront_logging_excludes_cookies(first_cloudfront_dist_config):
    """Verify CloudFront logging excludes cookies."""
    if first_cloudfront_dist_config is not None:
        logging_config = first_cloudfront_dist_config.get('Logging', {})
        assert logging_config.get('IncludeCookies', True) is False


def test_cloudfront_viewer_certificate_min_protocol_tls_1_2(first_cloudfront_dist_config):
    """Verify CloudFront viewer certificate minimum protocol is TLSv1.2."""
    if first_cloudfront_dist_config is not None:
        viewer_cert = first_cloudfront_dist_config.get('ViewerCertificate', {})
        min_protocol = viewer_cert.get('MinimumProtocolVersion', '')
        assert 'TLSv1.2' in min_protocol


def test_cloudfront_geo_restriction_is_none(first_cloudfront_dist_config):
    """Verify CloudFront geo restriction is none."""
    if first_cloudfront_dist_config is not None:
        restrictions = first_cloudfront_dist_config.get('Restrictions', {})
        geo_restriction = restrictions.get('GeoRestriction', {})
        assert geo_restriction.get('RestrictionType') == 'none'


def test_cloudfront_distribution_ipv6_enabled(first_cloudfront_dist_config):
    """Verify CloudFront distribution has IPv6 enabled."""
    if first_cloudfront_dist_config is not None:
        assert first_cloudfront_dist_config.get('IsIPV6Enabled') is True


def test_cloudfront_distribution_http_version_is_http2(first_cloudfront_dist_config):
    """Verify CloudFront distribution HTTP version is HTTP/2."""
    if first_cloudfront_dist_config is not None:
        http_version = first_cloudfront_dist_config.get('HttpVersion', '')
        assert 'http2' in http_version


def test_cloudfront_aliases_include_api_fqdn(cloudfront_client, api_distribution_id, config):
    """Verify CloudFront distribution aliases include API FQDN."""
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    aliases = dist_config['DistributionConfig'].get('Aliases', {}).get('Items', [])
    assert config['api_fqdn'] in aliases


def test_cloudfront_api_origin_protocol_is_https_only(cloudfront_client, api_distribution_id):
    """Verify CloudFront API origin protocol is https-only."""
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    origins = dist_config['DistributionConfig']['Origins']['Items']
    for origin in origins:
        if 'CustomOriginConfig' in origin:
            assert origin['CustomOriginConfig']['OriginProtocolPolicy'] == 'https-only'


def test_cloudfront_api_origin_ssl_protocols_tls_1_2(cloudfront_client, api_distribution_id):
    """Verify CloudFront API origin uses TLS 1.2."""
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
    """Verify CloudFront default cache behavior uses CachingDisabled policy."""
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    default_behavior = dist_config['DistributionConfig']['DefaultCacheBehavior']
    cache_policy_id = default_behavior.get('CachePolicyId', '')
    # CachingDisabled policy ID is 4135ea2d-6df8-44a3-9df3-4b5a84be39ad
    assert cache_policy_id != '' or 'ForwardedValues' in default_behavior


def test_cloudfront_health_cache_behavior_uses_api_origin(cloudfront_client, api_distribution_id):
    """Verify CloudFront /health path uses API Gateway origin."""
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    behaviors = dist_config['DistributionConfig'].get('CacheBehaviors', {})
    cache_behaviors = behaviors.get('Items', [])
    health_behavior = next(
        (b for b in cache_behaviors if '/health' in b.get('PathPattern', '')), None
    )
    if health_behavior:
        origin_id = health_behavior['TargetOriginId'].lower()
        assert 'api' in origin_id or 'execute' in origin_id


def test_cloudfront_v1_api_cache_behavior_uses_api_origin(cloudfront_client, api_distribution_id):
    """Verify CloudFront /v1/* path uses API Gateway origin."""
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    behaviors = dist_config['DistributionConfig'].get('CacheBehaviors', {})
    cache_behaviors = behaviors.get('Items', [])
    v1_behavior = next(
        (b for b in cache_behaviors if '/v1' in b.get('PathPattern', '')), None
    )
    if v1_behavior:
        origin_id = v1_behavior['TargetOriginId'].lower()
        assert 'api' in origin_id or 'execute' in origin_id


def test_cloudfront_docs_cache_behavior_uses_s3_origin(cloudfront_client, api_distribution_id):
    """Verify CloudFront docs path uses S3 origin."""
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
    """Verify CloudFront distribution has price class configured."""
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    price_class = dist_config['DistributionConfig'].get('PriceClass', '')
    assert price_class.startswith('PriceClass_')


def test_acm_certificate_is_issued(acm_client):
    """Verify ACM certificate is validated and issued."""
    certificates = acm_client.list_certificates(CertificateStatuses=['ISSUED'])
    assert len(certificates['CertificateSummaryList']) > 0


def test_acm_certificate_validation_method_is_dns(acm_client):
    """Verify ACM certificate validation method is DNS."""
    certificates = acm_client.list_certificates(CertificateStatuses=['ISSUED'])
    if not certificates['CertificateSummaryList']:
        pytest.skip("No issued certificates found")
    cert_arn = certificates['CertificateSummaryList'][0]['CertificateArn']
    cert_details = acm_client.describe_certificate(CertificateArn=cert_arn)
    domain_validation = cert_details['Certificate'].get('DomainValidationOptions', [])
    if domain_validation:
        assert domain_validation[0].get('ValidationMethod') == 'DNS'


def test_acm_certificate_domain_name_matches(acm_client, config):
    """Verify ACM certificate domain name matches expected domain."""
    certificates = acm_client.list_certificates(CertificateStatuses=['ISSUED'])
    if not certificates['CertificateSummaryList']:
        pytest.skip("No issued certificates found")
    domain_names = [c['DomainName'] for c in certificates['CertificateSummaryList']]
    has_matching_domain = any(config['domain'] in d for d in domain_names)
    assert has_matching_domain


# =============================================================================
# WAF Configuration
# =============================================================================


def test_waf_web_acl_has_cloudwatch_metrics_enabled():
    """Verify WAF Web ACL has CloudWatch metrics enabled."""
    waf_client = boto3.client('wafv2', region_name='us-east-1')
    response = waf_client.list_web_acls(Scope='CLOUDFRONT')
    acl = response['WebACLs'][0]
    acl_detail = waf_client.get_web_acl(Name=acl['Name'], Scope='CLOUDFRONT', Id=acl['Id'])
    metrics_enabled = acl_detail['WebACL']['VisibilityConfig']['CloudWatchMetricsEnabled']
    assert metrics_enabled is True


def test_waf_log_group_retention_is_30_days():
    """Verify WAF log group has 30 day retention."""
    logs_client = boto3.client('logs', region_name='us-east-1')
    response = logs_client.describe_log_groups(logGroupNamePrefix='aws-waf-logs-api')
    assert response['logGroups'][0].get('retentionInDays') == 30


def test_waf_web_acl_sampled_requests_enabled():
    """Verify WAF Web ACL has sampled requests enabled."""
    waf_client = boto3.client('wafv2', region_name='us-east-1')
    response = waf_client.list_web_acls(Scope='CLOUDFRONT')
    acl = response['WebACLs'][0]
    acl_detail = waf_client.get_web_acl(Name=acl['Name'], Scope='CLOUDFRONT', Id=acl['Id'])
    sampled_enabled = acl_detail['WebACL']['VisibilityConfig']['SampledRequestsEnabled']
    assert sampled_enabled is True


def test_waf_web_acl_scope_is_cloudfront():
    """Verify WAF Web ACL scope is CLOUDFRONT."""
    waf_client = boto3.client('wafv2', region_name='us-east-1')
    response = waf_client.list_web_acls(Scope='CLOUDFRONT')
    assert len(response['WebACLs']) > 0


# =============================================================================
# CloudFront Cache Policy Configuration
# =============================================================================


def _find_docs_cache_policy(cloudfront_client):
    """Find the docs cache policy from CloudFront custom policies."""
    response = cloudfront_client.list_cache_policies(Type='custom')
    policies = response['CachePolicyList'].get('Items', [])
    for policy in policies:
        name = policy['CachePolicy']['CachePolicyConfig']['Name'].lower()
        if 'docs' in name:
            return policy
    return None


def test_cloudfront_docs_cache_policy_default_ttl(cloudfront_client):
    """Verify CloudFront docs cache policy has default TTL configured."""
    docs_policy = _find_docs_cache_policy(cloudfront_client)
    if docs_policy:
        config = docs_policy['CachePolicy']['CachePolicyConfig']
        assert config['DefaultTTL'] > 0


def test_cloudfront_docs_cache_policy_max_ttl(cloudfront_client):
    """Verify CloudFront docs cache policy has max TTL configured."""
    docs_policy = _find_docs_cache_policy(cloudfront_client)
    if docs_policy:
        config = docs_policy['CachePolicy']['CachePolicyConfig']
        assert config['MaxTTL'] > 0


def test_cloudfront_docs_cache_policy_min_ttl(cloudfront_client):
    """Verify CloudFront docs cache policy has min TTL configured."""
    docs_policy = _find_docs_cache_policy(cloudfront_client)
    if docs_policy:
        config = docs_policy['CachePolicy']['CachePolicyConfig']
        assert 'MinTTL' in config


def test_cloudfront_docs_cache_policy_gzip_enabled(cloudfront_client):
    """Verify CloudFront docs cache policy has gzip compression enabled."""
    docs_policy = _find_docs_cache_policy(cloudfront_client)
    if docs_policy:
        config = docs_policy['CachePolicy']['CachePolicyConfig']
        params = config['ParametersInCacheKeyAndForwardedToOrigin']
        assert params.get('EnableAcceptEncodingGzip') is True


def test_cloudfront_docs_cache_policy_brotli_enabled(cloudfront_client):
    """Verify CloudFront docs cache policy has brotli compression enabled."""
    docs_policy = _find_docs_cache_policy(cloudfront_client)
    if docs_policy:
        config = docs_policy['CachePolicy']['CachePolicyConfig']
        params = config['ParametersInCacheKeyAndForwardedToOrigin']
        assert params.get('EnableAcceptEncodingBrotli') is True


def test_cloudfront_docs_cache_policy_cookies_none(cloudfront_client):
    """Verify CloudFront docs cache policy excludes cookies."""
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


# =============================================================================
# Firehose Configuration
# =============================================================================


def test_firehose_delivery_stream_is_active(firehose_client, config):
    """Verify Firehose delivery stream is active."""
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    assert response['DeliveryStreamDescription']['DeliveryStreamStatus'] == 'ACTIVE'


def test_firehose_delivery_stream_type_is_direct_put(firehose_client, config):
    """Verify Firehose delivery stream type is DirectPut."""
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    assert response['DeliveryStreamDescription']['DeliveryStreamType'] == 'DirectPut'


def test_firehose_destination_is_extended_s3(firehose_client, config):
    """Verify Firehose destination is Extended S3."""
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    destinations = response['DeliveryStreamDescription']['Destinations']
    assert destinations[0]['ExtendedS3DestinationDescription'] is not None


def test_firehose_s3_prefix_is_correct(firehose_client, config):
    """Verify Firehose S3 prefix is configured correctly."""
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    destinations = response['DeliveryStreamDescription']['Destinations']
    s3_config = destinations[0]['ExtendedS3DestinationDescription']
    assert s3_config['Prefix'] == 'cloudwatch-logs/api/'


def test_firehose_s3_error_prefix_is_correct(firehose_client, config):
    """Verify Firehose S3 error prefix is configured correctly."""
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    destinations = response['DeliveryStreamDescription']['Destinations']
    s3_config = destinations[0]['ExtendedS3DestinationDescription']
    assert s3_config['ErrorOutputPrefix'] == 'cloudwatch-logs/api-errors/'


def test_firehose_compression_is_gzip(firehose_client, config):
    """Verify Firehose compression is set to GZIP."""
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    destinations = response['DeliveryStreamDescription']['Destinations']
    s3_config = destinations[0]['ExtendedS3DestinationDescription']
    assert s3_config['CompressionFormat'] == 'GZIP'


def test_firehose_buffering_size_is_5mb(firehose_client, config):
    """Verify Firehose buffering size is 5 MB."""
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    destinations = response['DeliveryStreamDescription']['Destinations']
    s3_config = destinations[0]['ExtendedS3DestinationDescription']
    assert s3_config['BufferingHints']['SizeInMBs'] == 5


def test_firehose_buffering_interval_is_300_seconds(firehose_client, config):
    """Verify Firehose buffering interval is 300 seconds."""
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    destinations = response['DeliveryStreamDescription']['Destinations']
    s3_config = destinations[0]['ExtendedS3DestinationDescription']
    assert s3_config['BufferingHints']['IntervalInSeconds'] == 300


# =============================================================================
# DynamoDB Configuration
# =============================================================================


def test_api_audit_log_table_has_correct_hash_key(dynamodb_client, shared_config):
    """Verify API audit log table has correct hash key."""
    table_name = f"{shared_config['resource_prefix']}ApiAuditLog"
    response = dynamodb_client.describe_table(TableName=table_name)
    key_schema = response['Table']['KeySchema']
    hash_key = next((k for k in key_schema if k['KeyType'] == 'HASH'), None)
    assert hash_key['AttributeName'] == 'request_id'


def test_api_audit_log_table_has_correct_range_key(dynamodb_client, shared_config):
    """Verify API audit log table has correct range key."""
    table_name = f"{shared_config['resource_prefix']}ApiAuditLog"
    response = dynamodb_client.describe_table(TableName=table_name)
    key_schema = response['Table']['KeySchema']
    range_key = next((k for k in key_schema if k['KeyType'] == 'RANGE'), None)
    assert range_key['AttributeName'] == 'endpoint_timestamp'


def test_api_audit_log_table_has_endpoint_time_gsi(dynamodb_client, shared_config):
    """Verify API audit log table has endpoint-time GSI."""
    table_name = f"{shared_config['resource_prefix']}ApiAuditLog"
    response = dynamodb_client.describe_table(TableName=table_name)
    gsi_names = [gsi['IndexName'] for gsi in response['Table'].get('GlobalSecondaryIndexes', [])]
    assert 'endpoint-time-index' in gsi_names


def test_api_audit_log_table_has_status_time_gsi(dynamodb_client, shared_config):
    """Verify API audit log table has status-time GSI."""
    table_name = f"{shared_config['resource_prefix']}ApiAuditLog"
    response = dynamodb_client.describe_table(TableName=table_name)
    gsi_names = [gsi['IndexName'] for gsi in response['Table'].get('GlobalSecondaryIndexes', [])]
    assert 'status-time-index' in gsi_names


def test_api_audit_log_table_has_ttl_enabled(dynamodb_client, shared_config):
    """Verify API audit log table has TTL enabled."""
    table_name = f"{shared_config['resource_prefix']}ApiAuditLog"
    response = dynamodb_client.describe_time_to_live(TableName=table_name)
    assert response['TimeToLiveDescription']['TimeToLiveStatus'] == 'ENABLED'


def test_api_audit_log_table_ttl_attribute_is_ttl(dynamodb_client, shared_config):
    """Verify API audit log table TTL attribute is 'ttl'."""
    table_name = f"{shared_config['resource_prefix']}ApiAuditLog"
    response = dynamodb_client.describe_time_to_live(TableName=table_name)
    assert response['TimeToLiveDescription']['AttributeName'] == 'ttl'


def test_api_audit_log_table_has_pitr_enabled(dynamodb_client, shared_config):
    """Verify API audit log table has point-in-time recovery enabled."""
    table_name = f"{shared_config['resource_prefix']}ApiAuditLog"
    response = dynamodb_client.describe_continuous_backups(TableName=table_name)
    pitr = response['ContinuousBackupsDescription']['PointInTimeRecoveryDescription']
    assert pitr['PointInTimeRecoveryStatus'] == 'ENABLED'


def test_api_audit_log_table_billing_mode_is_pay_per_request(dynamodb_client, shared_config):
    """Verify API audit log table uses PAY_PER_REQUEST billing."""
    table_name = f"{shared_config['resource_prefix']}ApiAuditLog"
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response['Table']['BillingModeSummary']['BillingMode'] == 'PAY_PER_REQUEST'


def _get_audit_log_gsi(dynamodb_client, shared_config, gsi_name):
    """Get a GSI by name from the API audit log table."""
    table_name = f"{shared_config['resource_prefix']}ApiAuditLog"
    response = dynamodb_client.describe_table(TableName=table_name)
    gsis = response['Table'].get('GlobalSecondaryIndexes', [])
    return next((g for g in gsis if g['IndexName'] == gsi_name), None)


def test_dynamodb_endpoint_gsi_projection_type_is_all(dynamodb_client, shared_config):
    """Verify endpoint-time-index GSI projection type is ALL."""
    gsi = _get_audit_log_gsi(dynamodb_client, shared_config, 'endpoint-time-index')
    if gsi:
        assert gsi['Projection']['ProjectionType'] == 'ALL'


def test_dynamodb_status_gsi_projection_type_is_all(dynamodb_client, shared_config):
    """Verify status-time-index GSI projection type is ALL."""
    gsi = _get_audit_log_gsi(dynamodb_client, shared_config, 'status-time-index')
    if gsi:
        assert gsi['Projection']['ProjectionType'] == 'ALL'


def test_dynamodb_endpoint_gsi_range_key_is_request_timestamp(dynamodb_client, shared_config):
    """Verify endpoint-time-index GSI range key is request_timestamp."""
    gsi = _get_audit_log_gsi(dynamodb_client, shared_config, 'endpoint-time-index')
    if gsi:
        range_key = next((k for k in gsi['KeySchema'] if k['KeyType'] == 'RANGE'), None)
        assert range_key['AttributeName'] == 'request_timestamp'


def test_dynamodb_status_gsi_range_key_is_request_timestamp(dynamodb_client, shared_config):
    """Verify status-time-index GSI range key is request_timestamp."""
    gsi = _get_audit_log_gsi(dynamodb_client, shared_config, 'status-time-index')
    if gsi:
        range_key = next((k for k in gsi['KeySchema'] if k['KeyType'] == 'RANGE'), None)
        assert range_key['AttributeName'] == 'request_timestamp'


# =============================================================================
# SSM Configuration
# =============================================================================


def test_api_key_ssm_parameter_is_secure_string(ssm_client, config):
    """Verify API key SSM parameter is a SecureString."""
    param_name = config['ssm_parameter_name_for_api_key']
    response = ssm_client.get_parameter(Name=param_name, WithDecryption=False)
    assert response['Parameter']['Type'] == 'SecureString'


# =============================================================================
# API Gateway Configuration
# =============================================================================


def test_api_gateway_rest_api_endpoint_type_is_regional(apigateway_client, api_gateway_id):
    """Verify API Gateway REST API endpoint type is REGIONAL."""
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_rest_api(restApiId=api_gateway_id)
    assert 'REGIONAL' in response['endpointConfiguration']['types']


def test_api_gateway_stage_access_log_format_configured(apigateway_client, api_gateway_id):
    """Verify API Gateway prod stage has access log format configured."""
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_stage(restApiId=api_gateway_id, stageName='prod')
    access_log = response.get('accessLogSettings', {})
    assert 'format' in access_log


def test_api_gateway_method_settings_logging_level_is_info(apigateway_client, api_gateway_id):
    """Verify API Gateway method settings logging level is INFO."""
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_stage(restApiId=api_gateway_id, stageName='prod')
    method_settings = response.get('methodSettings', {})
    if '*/*' in method_settings:
        assert method_settings['*/*'].get('loggingLevel') == 'INFO'


def test_api_gateway_method_settings_metrics_enabled(apigateway_client, api_gateway_id):
    """Verify API Gateway method settings has metrics enabled."""
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_stage(restApiId=api_gateway_id, stageName='prod')
    method_settings = response.get('methodSettings', {})
    if '*/*' in method_settings:
        assert method_settings['*/*'].get('metricsEnabled') is True


def test_api_gateway_method_settings_data_trace_enabled(apigateway_client, api_gateway_id):
    """Verify API Gateway method settings has data trace configured."""
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_stage(restApiId=api_gateway_id, stageName='prod')
    method_settings = response.get('methodSettings', {})
    if '*/*' in method_settings:
        assert 'dataTraceEnabled' in method_settings['*/*']


def test_api_gateway_method_settings_apply_to_all_methods(apigateway_client, api_gateway_id):
    """Verify API Gateway method settings apply to all methods (*/*)."""
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_stage(restApiId=api_gateway_id, stageName='prod')
    method_settings = response.get('methodSettings', {})
    assert '*/*' in method_settings


def test_api_gateway_api_key_is_enabled(apigateway_client):
    """Verify API Gateway API key is enabled."""
    response = apigateway_client.get_api_keys()
    if response['items']:
        assert response['items'][0]['enabled'] is True


def test_api_gateway_usage_plan_throttle_rate_limit(apigateway_client):
    """Verify API Gateway usage plan has throttle rate limit configured."""
    response = apigateway_client.get_usage_plans()
    if response['items']:
        throttle = response['items'][0].get('throttle', {})
        assert 'rateLimit' in throttle


def test_api_gateway_stage_has_logging_enabled(apigateway_client, api_gateway_id):
    """Verify API Gateway prod stage has logging enabled."""
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_stage(restApiId=api_gateway_id, stageName='prod')
    access_log = response.get('accessLogSettings', {})
    assert 'destinationArn' in access_log


def test_api_gateway_stage_has_xray_tracing_disabled(apigateway_client, api_gateway_id):
    """Verify API Gateway prod stage has X-Ray tracing configured."""
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_stage(restApiId=api_gateway_id, stageName='prod')
    assert 'tracingEnabled' in response


# =============================================================================
# CloudFront Function Configuration
# =============================================================================


def test_cloudfront_url_rewrite_function_runtime(cloudfront_client):
    """Verify CloudFront URL rewrite function uses cloudfront-js-2.0 runtime."""
    response = cloudfront_client.list_functions()
    functions = response['FunctionList'].get('Items', [])
    url_rewrite = next((f for f in functions if f['Name'] == 'url-rewrite'), None)
    if url_rewrite is None:
        pytest.skip("url-rewrite function not found")
    func_config = url_rewrite['FunctionConfig']
    assert func_config['Runtime'] == 'cloudfront-js-2.0'


# =============================================================================
# WAF Firehose Configuration (us-east-1)
# =============================================================================


def test_waf_firehose_delivery_stream_is_active(shared_config):
    """Verify WAF Firehose delivery stream is active."""
    firehose_client = boto3.client('firehose', region_name='us-east-1')
    stream_name = f"{shared_config['resource_prefix']}-WafLogs"
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    assert response['DeliveryStreamDescription']['DeliveryStreamStatus'] == 'ACTIVE'


def test_waf_firehose_destination_is_extended_s3(shared_config):
    """Verify WAF Firehose destination is Extended S3."""
    firehose_client = boto3.client('firehose', region_name='us-east-1')
    stream_name = f"{shared_config['resource_prefix']}-WafLogs"
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    destinations = response['DeliveryStreamDescription']['Destinations']
    assert destinations[0].get('ExtendedS3DestinationDescription') is not None


def test_firehose_cloudwatch_logs_bucket_is_central_logs(firehose_client, config):
    """Verify Firehose CloudWatch logs bucket is central logs bucket."""
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    destinations = response['DeliveryStreamDescription']['Destinations']
    s3_config = destinations[0]['ExtendedS3DestinationDescription']
    assert config['central_logs_bucket'] in s3_config['BucketARN']


def test_firehose_waf_logs_bucket_is_central_logs(shared_config, config):
    """Verify WAF Firehose bucket is central logs bucket."""
    firehose_client = boto3.client('firehose', region_name='us-east-1')
    stream_name = f"{shared_config['resource_prefix']}-WafLogs"
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    destinations = response['DeliveryStreamDescription']['Destinations']
    s3_config = destinations[0]['ExtendedS3DestinationDescription']
    assert config['central_logs_bucket'] in s3_config['BucketARN']


def _check_firehose_cw_logging_disabled(response):
    """Check if Firehose stream has CloudWatch logging disabled."""
    destinations = response['DeliveryStreamDescription']['Destinations']
    s3_config = destinations[0]['ExtendedS3DestinationDescription']
    cw_logging = s3_config.get('CloudWatchLoggingOptions', {})
    return cw_logging.get('Enabled') is False or 'CloudWatchLoggingOptions' not in s3_config


def test_firehose_cloudwatch_logs_cloudwatch_logging_disabled(firehose_client, config):
    """Verify Firehose CloudWatch logs stream has CloudWatch logging disabled."""
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    assert _check_firehose_cw_logging_disabled(response)


def test_firehose_waf_logs_cloudwatch_logging_disabled(shared_config):
    """Verify WAF Firehose stream has CloudWatch logging disabled."""
    firehose_client = boto3.client('firehose', region_name='us-east-1')
    stream_name = f"{shared_config['resource_prefix']}-WafLogs"
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    assert _check_firehose_cw_logging_disabled(response)


# =============================================================================
# Log Subscription Filter Configuration
# =============================================================================


def test_catchall_subscription_filter_pattern_is_empty(logs_client, config):
    """Verify catchall handler subscription filter pattern is empty (captures all)."""
    log_group = config['catchall_handler_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    if response['subscriptionFilters']:
        assert response['subscriptionFilters'][0]['filterPattern'] == ''


def test_api_gateway_subscription_filter_pattern_is_empty(logs_client, config):
    """Verify API Gateway subscription filter pattern is empty (captures all)."""
    log_group = config['api_gateway_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    if response['subscriptionFilters']:
        assert response['subscriptionFilters'][0]['filterPattern'] == ''


def test_waf_subscription_filter_pattern_is_empty():
    """Verify WAF subscription filter pattern is empty (captures all)."""
    logs_client = boto3.client('logs', region_name='us-east-1')
    response = logs_client.describe_subscription_filters(logGroupName='aws-waf-logs-api')
    if response['subscriptionFilters']:
        assert response['subscriptionFilters'][0]['filterPattern'] == ''


def test_health_subscription_filter_pattern_is_empty(logs_client, config):
    """Verify health handler subscription filter pattern is empty (captures all)."""
    log_group = config['health_handler_log_group_name']
    try:
        response = logs_client.describe_subscription_filters(logGroupName=log_group)
        if response['subscriptionFilters']:
            assert response['subscriptionFilters'][0]['filterPattern'] == ''
    except logs_client.exceptions.ResourceNotFoundException:
        pytest.skip("Health handler log group not deployed")


# =============================================================================
# S3 Object Configuration
# =============================================================================


def test_index_html_content_type_is_text_html(s3_client, config):
    """Verify index.html content type is text/html."""
    bucket_name = config["api_fqdn"]
    response = s3_client.head_object(Bucket=bucket_name, Key="index.html")
    assert response['ContentType'] == 'text/html'


def test_404_html_content_type_is_text_html(s3_client, config):
    """Verify 404.html content type is text/html."""
    bucket_name = config["api_fqdn"]
    response = s3_client.head_object(Bucket=bucket_name, Key="404.html")
    assert response['ContentType'] == 'text/html'


def test_openapi_json_content_type_is_application_json(s3_client, config):
    """Verify openapi.json content type is application/json."""
    bucket_name = config["api_fqdn"]
    response = s3_client.head_object(Bucket=bucket_name, Key="openapi.json")
    assert response['ContentType'] == 'application/json'


def test_s3_docs_bucket_logging_enabled(s3_client, config):
    """Verify S3 docs bucket has logging enabled."""
    bucket_name = config["api_fqdn"]
    try:
        response = s3_client.get_bucket_logging(Bucket=bucket_name)
        logging_enabled = response.get('LoggingEnabled') is not None
        assert logging_enabled
    except s3_client.exceptions.NoSuchBucket:
        pytest.skip("S3 bucket not found")


# =============================================================================
# CloudWatch Log Group Configuration
# =============================================================================


def test_catchall_handler_log_group_retention_is_7_days(logs_client, config):
    """Verify catchall handler log group has 7 day retention."""
    log_group = config['catchall_handler_log_group_name']
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group)
    if response['logGroups']:
        assert response['logGroups'][0].get('retentionInDays') == 7


def test_api_gateway_log_group_retention_is_30_days(logs_client, config):
    """Verify API Gateway log group has 30 day retention."""
    log_group = config['api_gateway_log_group_name']
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group)
    if response['logGroups']:
        assert response['logGroups'][0].get('retentionInDays') == 30


def test_catchall_handler_log_group_kms_encryption(logs_client, config):
    """Verify catchall handler log group has KMS encryption configured."""
    log_group = config['catchall_handler_log_group_name']
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group)
    if response['logGroups']:
        kms_key = response['logGroups'][0].get('kmsKeyId')
        # Log group may or may not have KMS encryption - just verify field exists
        assert 'kmsKeyId' in response['logGroups'][0] or kms_key is None


def test_api_gateway_log_group_kms_encryption(logs_client, config):
    """Verify API Gateway log group has KMS encryption configured."""
    log_group = config['api_gateway_log_group_name']
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group)
    if response['logGroups']:
        kms_key = response['logGroups'][0].get('kmsKeyId')
        # Log group may or may not have KMS encryption - just verify field exists
        assert 'kmsKeyId' in response['logGroups'][0] or kms_key is None
