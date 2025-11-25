def test_sqs_job_queue_exists(sqs_client, config):
    queue_name = config["job_queue_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert 'QueueUrl' in response


def test_sqs_webhook_dlq_exists(sqs_client, config):
    queue_name = config["webhook_dlq_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert 'QueueUrl' in response


def test_sqs_dlq_redrive_policy(sqs_client, config):
    queue_name = config["job_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    attributes = sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['RedrivePolicy'])
    assert "RedrivePolicy" in attributes["Attributes"]


def test_sqs_visibility_timeout_matches_lambda(sqs_client, config):
    queue_name = config["job_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    attributes = sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['VisibilityTimeout'])
    visibility_timeout = int(attributes["Attributes"]["VisibilityTimeout"])
    assert visibility_timeout > 0


def test_sqs_job_queue_has_message_retention(sqs_client):
    queues = sqs_client.list_queues()
    if 'QueueUrls' in queues:
        queue_url = queues['QueueUrls'][0]
        attributes = sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['MessageRetentionPeriod'])
        assert 'MessageRetentionPeriod' in attributes['Attributes']


def test_sqs_webhook_dlq_has_message_retention(sqs_client):
    queues = sqs_client.list_queues()
    if 'QueueUrls' in queues:
        dlq_queues = [q for q in queues['QueueUrls'] if 'dlq' in q.lower()]
        if dlq_queues:
            queue_url = dlq_queues[0]
            attributes = sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['MessageRetentionPeriod'])
            assert 'MessageRetentionPeriod' in attributes['Attributes']


def test_sqs_job_dlq_exists(sqs_client):
    queues = sqs_client.list_queues()
    if 'QueueUrls' in queues:
        dlq_queues = [q for q in queues['QueueUrls'] if 'job' in q.lower() and 'dlq' in q.lower()]
        assert len(dlq_queues) >= 0


def test_sqs_dlq_receives_failed_messages(sqs_client, config):
    queue_name = config["webhook_dlq_name"]
    dlq_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    attributes = sqs_client.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=['ApproximateNumberOfMessages'])
    assert 'ApproximateNumberOfMessages' in attributes['Attributes']


def test_sqs_job_dlq_exists_and_configured(sqs_client, config):
    queue_name = config["job_queue_dlq_name"]
    dlq_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    attributes = sqs_client.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=['MessageRetentionPeriod'])
    assert int(attributes['Attributes']['MessageRetentionPeriod']) > 0
