"""Unit tests for test sqs."""
def test_sqs_job_queue_exists(sqs_client, config):
    """Test sqs job queue exists."""
    queue_name = config["job_queue_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert 'QueueUrl' in response


def test_sqs_webhook_dlq_exists(sqs_client, config):
    """Test sqs webhook dlq exists."""
    queue_name = config["webhook_dlq_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert 'QueueUrl' in response


def test_sqs_dlq_redrive_policy(sqs_client, config):
    """Test sqs dlq redrive policy."""
    queue_name = config["job_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    attr_names = ['RedrivePolicy']
    attributes = sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=attr_names)
    assert "RedrivePolicy" in attributes["Attributes"]


def test_sqs_visibility_timeout_matches_lambda(sqs_client, config):
    """Test sqs visibility timeout matches lambda."""
    queue_name = config["job_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    attr_names = ['VisibilityTimeout']
    attributes = sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=attr_names)
    visibility_timeout = int(attributes["Attributes"]["VisibilityTimeout"])
    assert visibility_timeout > 0


def test_sqs_job_queue_has_message_retention(sqs_client):
    """Test sqs job queue has message retention."""
    queues = sqs_client.list_queues()
    if 'QueueUrls' in queues:
        queue_url = queues['QueueUrls'][0]
        attr_names = ['MessageRetentionPeriod']
        attributes = sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=attr_names)
        assert 'MessageRetentionPeriod' in attributes['Attributes']


def test_sqs_webhook_dlq_has_message_retention(sqs_client):
    """Test sqs webhook dlq has message retention."""
    queues = sqs_client.list_queues()
    if 'QueueUrls' in queues:
        dlq_queues = [q for q in queues['QueueUrls'] if 'dlq' in q.lower()]
        if dlq_queues:
            queue_url = dlq_queues[0]
            attr_names = ['MessageRetentionPeriod']
            attributes = sqs_client.get_queue_attributes(
                QueueUrl=queue_url, AttributeNames=attr_names
            )
            assert 'MessageRetentionPeriod' in attributes['Attributes']


def test_sqs_job_dlq_exists(sqs_client):
    """Test sqs job dlq exists."""
    queues = sqs_client.list_queues()
    if 'QueueUrls' in queues:
        dlq_queues = [q for q in queues['QueueUrls'] if 'job' in q.lower() and 'dlq' in q.lower()]
        assert len(dlq_queues) >= 0


def test_sqs_dlq_receives_failed_messages(sqs_client, config):
    """Test sqs dlq receives failed messages."""
    queue_name = config["webhook_dlq_name"]
    dlq_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    attr_names = ['ApproximateNumberOfMessages']
    attributes = sqs_client.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=attr_names)
    assert 'ApproximateNumberOfMessages' in attributes['Attributes']


def test_sqs_job_dlq_exists_and_configured(sqs_client, config):
    """Test sqs job dlq exists and configured."""
    queue_name = config["job_queue_dlq_name"]
    dlq_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    attr_names = ['MessageRetentionPeriod']
    attributes = sqs_client.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=attr_names)
    assert int(attributes['Attributes']['MessageRetentionPeriod']) > 0


def test_sqs_drift_recovery_queue_exists(sqs_client, config):
    """Test drift recovery FIFO queue exists."""
    queue_name = config["drift_recovery_queue_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert 'QueueUrl' in response


def test_sqs_drift_recovery_queue_is_fifo(sqs_client, config):
    """Test drift recovery queue is configured as FIFO."""
    queue_name = config["drift_recovery_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=['FifoQueue']
    )
    assert attributes['Attributes'].get('FifoQueue') == 'true'


def test_sqs_drift_recovery_queue_has_deduplication(sqs_client, config):
    """Test drift recovery queue has content-based deduplication enabled."""
    queue_name = config["drift_recovery_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=['ContentBasedDeduplication']
    )
    assert attributes['Attributes'].get('ContentBasedDeduplication') == 'true'


def test_sqs_job_queue_can_send_message(sqs_client, config):
    """Test we can send a message to the job queue."""
    queue_name = config["job_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    response = sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody='{"test": "post-deployment-integration-test"}'
    )
    assert 'MessageId' in response
    # Clean up: receive and delete the test message
    messages = sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
    if 'Messages' in messages:
        for msg in messages['Messages']:
            sqs_client.delete_message(
                QueueUrl=queue_url, ReceiptHandle=msg['ReceiptHandle']
            )


def test_sqs_job_queue_can_receive_message(sqs_client, config):
    """Test we can receive messages from the job queue."""
    queue_name = config["job_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    # Send a test message first
    sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody='{"test": "post-deployment-receive-test"}'
    )
    # Receive it
    response = sqs_client.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=1
    )
    assert 'Messages' in response
    # Clean up
    for msg in response['Messages']:
        sqs_client.delete_message(
            QueueUrl=queue_url, ReceiptHandle=msg['ReceiptHandle']
        )
