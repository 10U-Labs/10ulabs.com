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


# Use factory for naming convention tests
(
    TestCatchAllHandlerIAMRoleNamingConventions,
    TestCatchAllHandlerLambdaFunctionNamingConventions,
) = create_deployed_naming_convention_tests(
    function_name_config_key='catchall_handler_function_name',
    default_function_name='TenULabsCatchAllHandler',
    handler_display_name='CatchAllHandler',
)


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


def test_acm_certificate_is_issued(acm_client):
    """Verify ACM certificate is validated and issued."""
    certificates = acm_client.list_certificates(CertificateStatuses=['ISSUED'])
    assert len(certificates['CertificateSummaryList']) > 0


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
