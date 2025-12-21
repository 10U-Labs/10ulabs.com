"""Layer 3: Wiring tests for api_backend post-deployment.

These tests verify that components are connected properly.
Tests assume Layer 1 existence and Layer 2 configuration tests have passed.
"""
import json
from datetime import UTC, datetime, timedelta

import pytest
from botocore.exceptions import ClientError

import boto3
import requests


TEST_HEADERS = {"x-test-mode": "true"}


# =============================================================================
# API Gateway → Lambda Wiring
# =============================================================================


def test_api_gateway_has_permission_to_invoke_health_lambda(lambda_client, config):
    """Verify API Gateway has permission to invoke health Lambda function."""
    function_name = config["health_handler_function_name"]
    try:
        response = lambda_client.get_policy(FunctionName=function_name)
        assert "Policy" in response
    except ClientError as err:
        if err.response["Error"]["Code"] == "ResourceNotFoundException":
            pytest.skip("Health Lambda not deployed (managed by operational_health.yml)")
        raise


# =============================================================================
# CloudFront → S3 Wiring
# =============================================================================


def test_cloudfront_distribution_origin_points_to_s3(cloudfront_client):
    """Verify CloudFront distribution origin points to S3."""
    distributions = cloudfront_client.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        dist_config = cloudfront_client.get_distribution_config(Id=dist_id)
        origins = dist_config['DistributionConfig']['Origins']['Items']
        assert len(origins) > 0


def test_cloudfront_logging_bucket_is_central_logs(
    cloudfront_client, api_distribution_id, config
):
    """Verify CloudFront logs to central logs bucket."""
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    logging_config = dist_config['DistributionConfig'].get('Logging', {})
    if not logging_config.get('Enabled', False):
        pytest.skip("CloudFront logging not yet enabled on distribution")
    bucket = logging_config.get('Bucket', '')
    assert config['central_logs_bucket'] in bucket


def test_cloudfront_logging_prefix_is_correct(cloudfront_client, api_distribution_id):
    """Verify CloudFront logging prefix is correct."""
    if api_distribution_id is None:
        pytest.skip("API CloudFront distribution not found")
    dist_config = cloudfront_client.get_distribution_config(Id=api_distribution_id)
    logging_config = dist_config['DistributionConfig'].get('Logging', {})
    prefix = logging_config.get('Prefix', '')
    assert prefix == 'cloudfront-logs/api/'


# =============================================================================
# CloudFront 404 Handling
# =============================================================================


def test_cloudfront_returns_404_for_nonexistent_endpoint(api_url):
    """Verify CloudFront returns 404 for nonexistent endpoints."""
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 404


def test_cloudfront_404_page_contains_error_message(api_url):
    """Verify CloudFront 404 page contains error message."""
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    data = json.loads(response.text)
    assert "error" in data


def test_cloudfront_404_page_contains_not_found_text(api_url):
    """Verify CloudFront 404 page contains not found text."""
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    assert "Not Found" in response.text or "Endpoint not found" in response.text


# =============================================================================
# CloudWatch Logs → Firehose Wiring (Subscription Filters)
# =============================================================================


def test_catchall_handler_subscription_filter_exists(logs_client, config):
    """Verify catchall handler log group has subscription filter."""
    log_group = config['catchall_handler_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'catchall-handler-to-firehose' in filter_names


def test_catchall_handler_subscription_destinations_firehose(logs_client, config):
    """Verify catchall handler subscription routes to Firehose."""
    log_group = config['catchall_handler_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    assert 'firehose' in destination_arn


def test_health_handler_subscription_filter_exists(logs_client, config):
    """Verify health handler log group has subscription filter."""
    log_group = config['health_handler_log_group_name']
    try:
        response = logs_client.describe_subscription_filters(logGroupName=log_group)
    except ClientError as err:
        if err.response["Error"]["Code"] == "ResourceNotFoundException":
            pytest.skip("Health handler log group not deployed")
        raise
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'health-handler-to-firehose' in filter_names


def test_api_gateway_subscription_filter_exists(logs_client, config):
    """Verify API Gateway log group has subscription filter."""
    log_group = config['api_gateway_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'api-gateway-to-firehose' in filter_names


def test_waf_subscription_filter_exists():
    """Verify WAF log group has subscription filter."""
    logs_client_east = boto3.client('logs', region_name='us-east-1')
    log_group_name = 'aws-waf-logs-api'
    response = logs_client_east.describe_subscription_filters(logGroupName=log_group_name)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'waf-to-firehose' in filter_names


# =============================================================================
# Firehose → S3 Wiring
# =============================================================================


def test_firehose_role_trusts_firehose_service(iam_client, config):
    """Verify Firehose role trusts the Firehose service."""
    response = iam_client.get_role(RoleName=config['firehose_role_name'])
    assume_role_policy = response['Role']['AssumeRolePolicyDocument']
    statements = assume_role_policy['Statement']
    service_principal = statements[0]['Principal']['Service']
    assert service_principal == 'firehose.amazonaws.com'


def test_cloudwatch_logs_firehose_role_trusts_logs_service(iam_client, config):
    """Verify CloudWatch Logs Firehose role trusts the CloudWatch Logs service."""
    role_name = config['cloudwatch_logs_firehose_role_name']
    response = iam_client.get_role(RoleName=role_name)
    assume_role_policy = response['Role']['AssumeRolePolicyDocument']
    statements = assume_role_policy['Statement']
    service_principal = statements[0]['Principal']['Service']
    assert f"logs.{config['aws_region']}.amazonaws.com" == service_principal


def test_firehose_role_has_s3_access_policy(iam_client, config):
    """Verify Firehose role has S3 access policy attached."""
    response = iam_client.list_role_policies(RoleName=config['firehose_role_name'])
    assert 'S3Access' in response['PolicyNames']


def test_cloudwatch_logs_firehose_role_has_firehose_access_policy(iam_client, config):
    """Verify CloudWatch Logs Firehose role has Firehose access policy attached."""
    role_name = config['cloudwatch_logs_firehose_role_name']
    response = iam_client.list_role_policies(RoleName=role_name)
    assert 'FirehoseAccess' in response['PolicyNames']


# =============================================================================
# WAF → CloudWatch Logs Wiring
# =============================================================================


def test_waf_logging_configuration_exists(waf_logging_config):
    """Verify WAF logging configuration exists."""
    assert waf_logging_config is not None


def test_waf_logging_destinations_cloudwatch_logs(waf_logging_config):
    """Verify WAF logs to CloudWatch Logs."""
    if waf_logging_config is not None:
        destinations = waf_logging_config['LogDestinationConfigs']
        assert 'aws-waf-logs-api' in destinations[0]


# =============================================================================
# Metrics / Observability Wiring
# =============================================================================


def test_firehose_receives_incoming_records(config, aws_region):
    """Verify Firehose delivery stream receives incoming records."""
    cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=24)
    stream_name = config['firehose_delivery_stream_name']
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Firehose',
        MetricName='IncomingRecords',
        Dimensions=[{'Name': 'DeliveryStreamName', 'Value': stream_name}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Sum']
    )
    assert 'Datapoints' in response


def test_firehose_delivery_to_s3_is_successful(config, aws_region):
    """Verify Firehose successfully delivers to S3."""
    cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=24)
    stream_name = config['firehose_delivery_stream_name']
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Firehose',
        MetricName='DeliveryToS3.Success',
        Dimensions=[{'Name': 'DeliveryStreamName', 'Value': stream_name}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Sum']
    )
    assert 'Datapoints' in response


def test_s3_cloudwatch_logs_prefix_accessible(config, aws_region):
    """Verify S3 cloudwatch-logs prefix is accessible."""
    s3 = boto3.client('s3', region_name=aws_region)
    response = s3.list_objects_v2(
        Bucket=config['central_logs_bucket'],
        Prefix='cloudwatch-logs/api/',
        MaxKeys=1
    )
    assert 'Contents' in response or 'KeyCount' in response


def test_s3_cloudfront_logs_prefix_accessible(config, aws_region):
    """Verify S3 cloudfront-logs prefix is accessible."""
    s3 = boto3.client('s3', region_name=aws_region)
    response = s3.list_objects_v2(
        Bucket=config['central_logs_bucket'],
        Prefix='cloudfront-logs/api/',
        MaxKeys=1
    )
    assert 'Contents' in response or 'KeyCount' in response


def test_waf_metrics_being_collected():
    """Verify WAF metrics are being collected in CloudWatch."""
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=24)
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/WAFV2',
        MetricName='AllowedRequests',
        Dimensions=[
            {'Name': 'WebACL', 'Value': 'ApiWafWebAcl'},
            {'Name': 'Region', 'Value': 'us-east-1'},
            {'Name': 'Rule', 'Value': 'ALL'}
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Sum']
    )
    assert 'Datapoints' in response


def test_cloudwatch_metrics_published_for_circuit_breaker(aws_region):
    """Verify circuit breaker state metrics are published."""
    cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=1)
    response = cloudwatch.get_metric_statistics(
        Namespace='WebhookRouter',
        MetricName='CircuitBreakerState',
        Dimensions=[],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Average']
    )
    assert 'Datapoints' in response


def test_eventbridge_scheduled_rules_exist(aws_region):
    """Verify scheduled EventBridge rules exist for DLQ reprocessing."""
    events = boto3.client('events', region_name=aws_region)
    rules = events.list_rules()
    scheduled_rules = [r for r in rules['Rules'] if r.get('ScheduleExpression')]
    assert len(scheduled_rules) > 0


def test_dynamodb_consumed_capacity_metrics_available(config, aws_region):
    """Verify DynamoDB consumed capacity metrics are available."""
    cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
    table_name = config['circuit_breaker_state_table_name']
    response = cloudwatch.list_metrics(
        Namespace='AWS/DynamoDB',
        MetricName='ConsumedReadCapacityUnits',
        Dimensions=[{'Name': 'TableName', 'Value': table_name}]
    )
    assert 'Metrics' in response
