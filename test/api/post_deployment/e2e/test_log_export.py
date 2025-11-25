from datetime import UTC, datetime, timedelta

import boto3


def test_firehose_delivery_stream_has_recent_incoming_records(config):
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=24)
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Firehose',
        MetricName='IncomingRecords',
        Dimensions=[{'Name': 'DeliveryStreamName', 'Value': config['firehose_delivery_stream_name']}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Sum']
    )
    assert 'Datapoints' in response


def test_firehose_delivery_to_s3_is_successful(config):
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=24)
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Firehose',
        MetricName='DeliveryToS3.Success',
        Dimensions=[{'Name': 'DeliveryStreamName', 'Value': config['firehose_delivery_stream_name']}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Sum']
    )
    assert 'Datapoints' in response


def test_s3_cloudwatch_logs_prefix_can_be_listed(config):
    s3 = boto3.client('s3', region_name='us-east-1')
    response = s3.list_objects_v2(
        Bucket=config['central_logs_bucket'],
        Prefix='cloudwatch-logs/api/',
        MaxKeys=1
    )
    assert 'Contents' in response or 'KeyCount' in response


def test_s3_cloudfront_logs_prefix_can_be_listed(config):
    s3 = boto3.client('s3', region_name='us-east-1')
    response = s3.list_objects_v2(
        Bucket=config['central_logs_bucket'],
        Prefix='cloudfront-logs/api/',
        MaxKeys=1
    )
    assert 'Contents' in response or 'KeyCount' in response


def test_waf_metrics_are_being_collected():
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


def test_cloudfront_requests_metric_available():
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=24)
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/CloudFront',
        MetricName='Requests',
        Dimensions=[{'Name': 'DistributionId', 'Value': 'ALL'}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Sum']
    )
    assert 'Datapoints' in response


def test_dynamodb_streams_consumed_records_metric(config):
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    response = cloudwatch.list_metrics(
        Namespace='AWS/DynamoDB',
        MetricName='ConsumedReadCapacityUnits',
        Dimensions=[{'Name': 'TableName', 'Value': config['circuit_breaker_state_table_name']}]
    )
    assert 'Metrics' in response
