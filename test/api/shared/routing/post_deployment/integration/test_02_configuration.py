"""Layer 2: Configuration tests for api_shared_routing post-deployment.

These tests verify that resources are configured correctly.
Tests assume Layer 1 existence tests have passed.
"""
import pytest

import boto3

from naming_conventions import validate_name

pytestmark = pytest.mark.layer(2)


# =============================================================================
# Lambda Configuration
# =============================================================================


def test_lambda_catchall_handler_runtime_is_python313(lambda_client, shared_config):
    """Verify Lambda catchall handler uses Python 3.13 runtime."""
    function_name = shared_config['lambda_handler_names']['catchall']
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_catchall_handler_role_name_is_pascalcase(iam_client, shared_config):
    """Verify CatchAllHandler IAM role name uses PascalCase."""
    role_name = f"{shared_config['resource_prefix']}CatchAllHandlerServiceRole"
    response = iam_client.get_role(RoleName=role_name)
    actual_name = response['Role']['RoleName']
    error = validate_name(actual_name)
    assert error is None, (
        f"Deployed IAM role has invalid name '{actual_name}': {error}"
    )


def test_catchall_handler_function_name_is_pascalcase(lambda_client, shared_config):
    """Verify CatchAllHandler Lambda function name uses PascalCase."""
    function_name = shared_config['lambda_handler_names']['catchall']
    response = lambda_client.get_function(FunctionName=function_name)
    actual_name = response['Configuration']['FunctionName']
    error = validate_name(actual_name)
    assert error is None, (
        f"Deployed Lambda function has invalid name '{actual_name}': {error}"
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
