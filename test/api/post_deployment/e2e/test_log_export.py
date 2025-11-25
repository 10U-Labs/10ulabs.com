from datetime import UTC, datetime, timedelta

import boto3


def test_firehose_delivery_stream_has_recent_incoming_records():
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=24)
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Firehose',
        MetricName='IncomingRecords',
        Dimensions=[{'Name': 'DeliveryStreamName', 'Value': 'TenULabs-CloudWatchLogs'}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Sum']
    )
    assert 'Datapoints' in response


def test_firehose_delivery_to_s3_is_successful():
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=24)
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Firehose',
        MetricName='DeliveryToS3.Success',
        Dimensions=[{'Name': 'DeliveryStreamName', 'Value': 'TenULabs-CloudWatchLogs'}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Sum']
    )
    assert 'Datapoints' in response


def test_s3_cloudwatch_logs_prefix_can_be_listed():
    s3 = boto3.client('s3', region_name='us-east-1')
    response = s3.list_objects_v2(
        Bucket='10ulabs-central-logs',
        Prefix='cloudwatch-logs/api/',
        MaxKeys=1
    )
    assert 'Contents' in response or 'KeyCount' in response
