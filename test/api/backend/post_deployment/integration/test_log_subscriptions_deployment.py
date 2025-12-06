"""Tests for CloudWatch Logs subscription filter deployments."""
import pytest
from botocore.exceptions import ClientError


def test_health_handler_subscription_filter_exists(logs_client, config):
    """Verify health handler log group has subscription filter."""
    log_group = config['health_handler_log_group_name']
    try:
        response = logs_client.describe_subscription_filters(logGroupName=log_group)
    except ClientError as err:
        if err.response["Error"]["Code"] == "ResourceNotFoundException":
            pytest.skip("Health handler log group not deployed (managed by health.yml)")
        raise
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    has_filter = 'health-handler-to-firehose' in filter_names
    assert has_filter


def test_health_handler_subscription_destinations_firehose(logs_client, config):
    """Verify health handler subscription routes to Firehose."""
    log_group = config['health_handler_log_group_name']
    try:
        response = logs_client.describe_subscription_filters(logGroupName=log_group)
    except ClientError as err:
        if err.response["Error"]["Code"] == "ResourceNotFoundException":
            pytest.skip("Health handler log group not deployed (managed by health.yml)")
        raise
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    is_firehose = 'firehose' in destination_arn
    assert is_firehose


def test_catchall_handler_subscription_filter_exists(logs_client, config):
    """Verify catchall handler log group has subscription filter."""
    log_group = config['catchall_handler_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    has_filter = 'catchall-handler-to-firehose' in filter_names
    assert has_filter


def test_catchall_handler_subscription_destinations_firehose(logs_client, config):
    """Verify catchall handler subscription routes to Firehose."""
    log_group = config['catchall_handler_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    is_firehose = 'firehose' in destination_arn
    assert is_firehose


def test_api_gateway_subscription_filter_exists(logs_client, config):
    """Verify API Gateway log group has subscription filter."""
    log_group = config['api_gateway_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    has_filter = 'api-gateway-to-firehose' in filter_names
    assert has_filter


def test_api_gateway_subscription_destinations_firehose(logs_client, config):
    """Verify API Gateway subscription routes to Firehose."""
    log_group = config['api_gateway_log_group_name']
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    is_firehose = 'firehose' in destination_arn
    assert is_firehose


def test_waf_subscription_filter_exists():
    """Verify WAF log group has subscription filter."""
    logs_client_east = __import__('boto3').client('logs', region_name='us-east-1')
    log_group_name = 'aws-waf-logs-api'
    response = logs_client_east.describe_subscription_filters(logGroupName=log_group_name)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    has_filter = 'waf-to-firehose' in filter_names
    assert has_filter


def test_waf_subscription_destinations_firehose():
    """Verify WAF subscription routes to Firehose."""
    logs_client_east = __import__('boto3').client('logs', region_name='us-east-1')
    log_group_name = 'aws-waf-logs-api'
    response = logs_client_east.describe_subscription_filters(logGroupName=log_group_name)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    is_firehose = 'firehose' in destination_arn
    assert is_firehose
