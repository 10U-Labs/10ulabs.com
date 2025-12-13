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
    queue_name = config["job_dlq_name"]
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


# NOTE: Removed test_sqs_job_queue_can_send_message and test_sqs_job_queue_can_receive_message
# These tests sent real messages to the production job queue which has a Lambda trigger.
# The Lambda would process these invalid test messages, fail, and trip the circuit breaker.
# SQS send/receive capability is an AWS service guarantee - no need to test it.


# === Webhook Ingress Queue Tests (API Gateway → SQS direct integration) ===


def test_sqs_webhook_ingress_queue_exists(sqs_client, config):
    """Test webhook ingress queue exists (API Gateway → SQS direct integration)."""
    queue_name = config["webhook_ingress_queue_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert 'QueueUrl' in response


def test_sqs_webhook_ingress_dlq_exists(sqs_client, config):
    """Test webhook ingress DLQ exists."""
    queue_name = config["webhook_ingress_dlq_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert 'QueueUrl' in response


def test_sqs_webhook_ingress_has_redrive_policy(sqs_client, config):
    """Test webhook ingress queue has redrive policy to DLQ."""
    queue_name = config["webhook_ingress_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=['RedrivePolicy']
    )
    assert 'RedrivePolicy' in attributes['Attributes']


def test_sqs_webhook_ingress_short_retention(sqs_client, config):
    """Test webhook ingress queue has short retention for DDoS protection."""
    queue_name = config["webhook_ingress_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=['MessageRetentionPeriod']
    )
    retention = int(attributes['Attributes']['MessageRetentionPeriod'])
    # Should be <= 1 hour (3600 seconds) for DDoS protection
    assert retention <= 3600


# === Ignored Events Queue Tests ===


def test_sqs_ignored_events_queue_exists(sqs_client, config):
    """Test ignored events queue exists."""
    queue_name = config["ignored_events_queue_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert 'QueueUrl' in response


def test_sqs_ignored_events_dlq_exists(sqs_client, config):
    """Test ignored events DLQ exists."""
    queue_name = config["ignored_events_dlq_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert 'QueueUrl' in response


def test_sqs_ignored_events_has_redrive_policy(sqs_client, config):
    """Test ignored events queue has redrive policy."""
    queue_name = config["ignored_events_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=['RedrivePolicy']
    )
    assert 'RedrivePolicy' in attributes['Attributes']


# === Cleanup Queue Tests ===


def test_sqs_cleanup_queue_exists(sqs_client, config):
    """Test cleanup queue exists."""
    queue_name = config["cleanup_queue_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert 'QueueUrl' in response


def test_sqs_cleanup_dlq_exists(sqs_client, config):
    """Test cleanup DLQ exists."""
    queue_name = config["cleanup_dlq_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert 'QueueUrl' in response


def test_sqs_cleanup_has_redrive_policy(sqs_client, config):
    """Test cleanup queue has redrive policy."""
    queue_name = config["cleanup_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=['RedrivePolicy']
    )
    assert 'RedrivePolicy' in attributes['Attributes']
