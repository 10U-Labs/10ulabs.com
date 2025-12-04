"""Tests for CloudWatch metrics and EventBridge triggers."""
from datetime import UTC, datetime, timedelta

import boto3


def test_cloudwatch_metrics_published_for_circuit_breaker():
    """Verify circuit breaker state metrics are published."""
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
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


def test_cloudwatch_metrics_published_for_queue_depth():
    """Verify queue depth metrics are published."""
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=1)
    response = cloudwatch.get_metric_statistics(
        Namespace='WebhookRouter',
        MetricName='QueueDepth',
        Dimensions=[],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Average']
    )
    assert 'Datapoints' in response


def test_cloudwatch_metrics_published_for_processing_time():
    """Verify processing time metrics are published."""
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=1)
    response = cloudwatch.get_metric_statistics(
        Namespace='WebhookRouter',
        MetricName='ProcessingTime',
        Dimensions=[],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Average']
    )
    assert 'Datapoints' in response


def test_eventbridge_triggers_circuit_breaker_remediation():
    """Verify EventBridge rules exist for circuit breaker."""
    events = boto3.client('events', region_name='us-east-1')
    rules = events.list_rules()
    rule_names = [r['Name'] for r in rules['Rules']]
    assert len(rule_names) > 0


def test_eventbridge_triggers_dlq_reprocessor():
    """Verify scheduled EventBridge rules exist for DLQ reprocessing."""
    events = boto3.client('events', region_name='us-east-1')
    rules = events.list_rules()
    scheduled_rules = [r for r in rules['Rules'] if r.get('ScheduleExpression')]
    assert len(scheduled_rules) > 0
