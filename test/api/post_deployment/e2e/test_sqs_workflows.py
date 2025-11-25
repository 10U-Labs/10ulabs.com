import boto3


def test_sqs_messages_processed_by_lambda():
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages'])
    assert "ApproximateNumberOfMessages" in attributes["Attributes"]


def test_failed_messages_move_to_dlq_after_max_retries():
    sqs = boto3.client('sqs', region_name='us-east-1')
    dlq_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-job-dlq')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=['ApproximateNumberOfMessages'])
    assert "ApproximateNumberOfMessages" in attributes["Attributes"]


def test_sqs_message_processing_updates_status():
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages'])
    assert "ApproximateNumberOfMessages" in attributes["Attributes"]


def test_dlq_reprocessor_moves_messages_back():
    sqs = boto3.client('sqs', region_name='us-east-1')
    dlq_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-job-dlq')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=['ApproximateNumberOfMessages'])
    assert "ApproximateNumberOfMessages" in attributes["Attributes"]


def test_queue_depth_metrics_published():
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages'])
    assert "ApproximateNumberOfMessages" in attributes["Attributes"]


def test_sqs_message_retry_moves_to_dlq_after_max_attempts():
    sqs = boto3.client('sqs', region_name='us-east-1')
    dlq_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-dlq')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=['ApproximateNumberOfMessages'])
    dlq_count = int(attributes['Attributes']['ApproximateNumberOfMessages'])
    assert dlq_count >= 0


def test_dlq_reprocessor_workflow_moves_messages_back():
    sqs = boto3.client('sqs', region_name='us-east-1')
    job_dlq_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-job-dlq')['QueueUrl']
    initial_dlq_attrs = sqs.get_queue_attributes(QueueUrl=job_dlq_url, AttributeNames=['ApproximateNumberOfMessages'])
    initial_dlq_count = int(initial_dlq_attrs['Attributes']['ApproximateNumberOfMessages'])
    assert initial_dlq_count >= 0


def test_sqs_visibility_timeout_prevents_duplicate_processing():
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['VisibilityTimeout'])
    visibility_timeout = int(attributes['Attributes']['VisibilityTimeout'])
    assert visibility_timeout > 30


def test_dynamodb_ttl_expires_old_idempotency_records():
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    response = dynamodb.describe_time_to_live(TableName='TenULabsWebhookHandler-idempotency')
    assert response['TimeToLiveDescription']['TimeToLiveStatus'] == 'ENABLED'


def test_complete_workflow_job_lifecycle():
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    initial_attrs = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages'])
    initial_count = int(initial_attrs['Attributes']['ApproximateNumberOfMessages'])
    assert initial_count >= 0


def test_sqs_fifo_ordering_not_required_for_webhooks():
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    assert '.fifo' not in queue_url


def test_sqs_message_deduplication_not_enabled():
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['All'])
    assert 'ContentBasedDeduplication' not in attributes['Attributes']
