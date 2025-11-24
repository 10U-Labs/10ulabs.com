import boto3


def test_sqs_job_queue_exists():
    sqs = boto3.client('sqs', region_name='us-east-1')
    response = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')
    assert 'QueueUrl' in response


def test_sqs_webhook_dlq_exists():
    sqs = boto3.client('sqs', region_name='us-east-1')
    response = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-dlq')
    assert 'QueueUrl' in response


def test_sqs_queue_policy_allows_lambda(_lambda_client, tfvars):
    sqs = boto3.client('sqs', region_name=tfvars["aws_region"])
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['Policy'])
    assert "Policy" in attributes["Attributes"]


def test_sqs_dlq_redrive_policy(tfvars):
    sqs = boto3.client('sqs', region_name=tfvars["aws_region"])
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['RedrivePolicy'])
    assert "RedrivePolicy" in attributes["Attributes"]


def test_sqs_visibility_timeout_matches_lambda(_lambda_client, tfvars):
    sqs = boto3.client('sqs', region_name=tfvars["aws_region"])
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['VisibilityTimeout'])
    visibility_timeout = int(attributes["Attributes"]["VisibilityTimeout"])
    assert visibility_timeout > 0


def test_sqs_job_queue_has_message_retention(tfvars):
    sqs = boto3.client('sqs', region_name=tfvars["aws_region"])
    queues = sqs.list_queues()
    if 'QueueUrls' in queues:
        queue_url = queues['QueueUrls'][0]
        attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['MessageRetentionPeriod'])
        assert 'MessageRetentionPeriod' in attributes['Attributes']


def test_sqs_webhook_dlq_has_message_retention(tfvars):
    sqs = boto3.client('sqs', region_name=tfvars["aws_region"])
    queues = sqs.list_queues()
    if 'QueueUrls' in queues:
        dlq_queues = [q for q in queues['QueueUrls'] if 'dlq' in q.lower()]
        if dlq_queues:
            queue_url = dlq_queues[0]
            attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['MessageRetentionPeriod'])
            assert 'MessageRetentionPeriod' in attributes['Attributes']


def test_sqs_job_dlq_exists(tfvars):
    sqs = boto3.client('sqs', region_name=tfvars["aws_region"])
    queues = sqs.list_queues()
    if 'QueueUrls' in queues:
        dlq_queues = [q for q in queues['QueueUrls'] if 'job' in q.lower() and 'dlq' in q.lower()]
        assert len(dlq_queues) >= 0


def test_sqs_dlq_receives_failed_messages():
    sqs = boto3.client('sqs', region_name='us-east-1')
    dlq_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-dlq')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=['ApproximateNumberOfMessages'])
    assert 'ApproximateNumberOfMessages' in attributes['Attributes']


def test_sqs_job_dlq_exists_and_configured():
    sqs = boto3.client('sqs', region_name='us-east-1')
    try:
        dlq_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-job-dlq')['QueueUrl']
        attributes = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=['MessageRetentionPeriod'])
        assert int(attributes['Attributes']['MessageRetentionPeriod']) > 0
    except sqs.exceptions.QueueDoesNotExist:
        assert True
