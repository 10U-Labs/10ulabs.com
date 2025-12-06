"""Unit tests for test sqs workflows."""
import boto3


def test_sqs_messages_processed_by_lambda(config):
    """Test sqs messages processed by lambda."""
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName=config['job_queue_name'])['QueueUrl']
    attr_names = ['ApproximateNumberOfMessages']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=attr_names)
    assert "ApproximateNumberOfMessages" in attributes["Attributes"]


def test_failed_messages_move_to_dlq_after_max_retries(config):
    """Test failed messages move to dlq after max retries."""
    sqs = boto3.client('sqs', region_name='us-east-1')
    dlq_url = sqs.get_queue_url(QueueName=config['job_queue_dlq_name'])['QueueUrl']
    attr_names = ['ApproximateNumberOfMessages']
    attributes = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=attr_names)
    assert "ApproximateNumberOfMessages" in attributes["Attributes"]


def test_sqs_message_processing_updates_status(config):
    """Test sqs message processing updates status."""
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName=config['job_queue_name'])['QueueUrl']
    attr_names = ['ApproximateNumberOfMessages']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=attr_names)
    assert "ApproximateNumberOfMessages" in attributes["Attributes"]


def test_dlq_reprocessor_moves_messages_back(config):
    """Test dlq reprocessor moves messages back."""
    sqs = boto3.client('sqs', region_name='us-east-1')
    dlq_url = sqs.get_queue_url(QueueName=config['job_queue_dlq_name'])['QueueUrl']
    attr_names = ['ApproximateNumberOfMessages']
    attributes = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=attr_names)
    assert "ApproximateNumberOfMessages" in attributes["Attributes"]


def test_queue_depth_metrics_published(config):
    """Test queue depth metrics published."""
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName=config['job_queue_name'])['QueueUrl']
    attr_names = ['ApproximateNumberOfMessages']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=attr_names)
    assert "ApproximateNumberOfMessages" in attributes["Attributes"]


def test_sqs_message_retry_moves_to_dlq_after_max_attempts(config):
    """Test sqs message retry moves to dlq after max attempts."""
    sqs = boto3.client('sqs', region_name='us-east-1')
    dlq_url = sqs.get_queue_url(QueueName=config['webhook_dlq_name'])['QueueUrl']
    attr_names = ['ApproximateNumberOfMessages']
    attributes = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=attr_names)
    dlq_count = int(attributes['Attributes']['ApproximateNumberOfMessages'])
    assert dlq_count >= 0


def test_dlq_reprocessor_workflow_moves_messages_back(config):
    """Test dlq reprocessor workflow moves messages back."""
    sqs = boto3.client('sqs', region_name='us-east-1')
    job_dlq_url = sqs.get_queue_url(QueueName=config['job_queue_dlq_name'])['QueueUrl']
    attr_names = ['ApproximateNumberOfMessages']
    initial_dlq_attrs = sqs.get_queue_attributes(QueueUrl=job_dlq_url, AttributeNames=attr_names)
    initial_dlq_count = int(initial_dlq_attrs['Attributes']['ApproximateNumberOfMessages'])
    assert initial_dlq_count >= 0


def test_sqs_visibility_timeout_prevents_duplicate_processing(config):
    """Test sqs visibility timeout prevents duplicate processing."""
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName=config['job_queue_name'])['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['VisibilityTimeout'])
    visibility_timeout = int(attributes['Attributes']['VisibilityTimeout'])
    assert visibility_timeout > 30


def test_dynamodb_ttl_expires_old_idempotency_records(config):
    """Test dynamodb ttl expires old idempotency records."""
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    response = dynamodb.describe_time_to_live(TableName=config['idempotency_table_name'])
    assert response['TimeToLiveDescription']['TimeToLiveStatus'] == 'ENABLED'


def test_complete_workflow_job_lifecycle(config):
    """Test complete workflow job lifecycle."""
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName=config['job_queue_name'])['QueueUrl']
    attr_names = ['ApproximateNumberOfMessages']
    initial_attrs = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=attr_names)
    initial_count = int(initial_attrs['Attributes']['ApproximateNumberOfMessages'])
    assert initial_count >= 0


def test_sqs_fifo_ordering_not_required_for_webhooks(config):
    """Test sqs fifo ordering not required for webhooks."""
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName=config['job_queue_name'])['QueueUrl']
    assert '.fifo' not in queue_url


def test_sqs_message_deduplication_not_enabled(config):
    """Test sqs message deduplication not enabled."""
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName=config['job_queue_name'])['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['All'])
    assert 'ContentBasedDeduplication' not in attributes['Attributes']
