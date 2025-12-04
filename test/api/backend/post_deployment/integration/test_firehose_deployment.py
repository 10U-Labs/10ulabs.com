"""Tests for Firehose delivery stream deployment and configuration."""


def test_firehose_delivery_stream_exists(firehose_client, config):
    """Verify Firehose delivery stream exists."""
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    assert response['DeliveryStreamDescription']['DeliveryStreamName'] == stream_name


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


def test_firehose_role_exists(iam_client, config):
    """Verify Firehose IAM role exists."""
    response = iam_client.get_role(RoleName=config['firehose_role_name'])
    assert response['Role']['RoleName'] == config['firehose_role_name']


def test_firehose_role_trusts_firehose_service(iam_client, config):
    """Verify Firehose role trusts the Firehose service."""
    response = iam_client.get_role(RoleName=config['firehose_role_name'])
    assume_role_policy = response['Role']['AssumeRolePolicyDocument']
    statements = assume_role_policy['Statement']
    service_principal = statements[0]['Principal']['Service']
    assert service_principal == 'firehose.amazonaws.com'


def test_cloudwatch_logs_firehose_role_exists(iam_client, config):
    """Verify CloudWatch Logs Firehose IAM role exists."""
    role_name = config['cloudwatch_logs_firehose_role_name']
    response = iam_client.get_role(RoleName=role_name)
    assert response['Role']['RoleName'] == role_name


def test_cloudwatch_logs_firehose_role_trusts_logs_service(iam_client, config):
    """Verify CloudWatch Logs Firehose role trusts the CloudWatch Logs service."""
    role_name = config['cloudwatch_logs_firehose_role_name']
    response = iam_client.get_role(RoleName=role_name)
    assume_role_policy = response['Role']['AssumeRolePolicyDocument']
    statements = assume_role_policy['Statement']
    service_principal = statements[0]['Principal']['Service']
    assert 'logs.us-east-1.amazonaws.com' == service_principal


def test_firehose_role_has_s3_access_policy(iam_client, config):
    """Verify Firehose role has S3 access policy attached."""
    response = iam_client.list_role_policies(RoleName=config['firehose_role_name'])
    assert 'S3Access' in response['PolicyNames']


def test_cloudwatch_logs_firehose_role_has_firehose_access_policy(iam_client, config):
    """Verify CloudWatch Logs Firehose role has Firehose access policy attached."""
    role_name = config['cloudwatch_logs_firehose_role_name']
    response = iam_client.list_role_policies(RoleName=role_name)
    assert 'FirehoseAccess' in response['PolicyNames']
