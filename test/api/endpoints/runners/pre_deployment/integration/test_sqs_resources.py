"""Tests to validate SQS resources exist for runners."""


def test_job_queue_exists(sqs_client):
    """Verify the job queue exists."""
    response = sqs_client.list_queues(QueueNamePrefix="10uLabs-JobQueue")
    queue_urls = response.get("QueueUrls", [])
    assert len(queue_urls) >= 1, "No job queue found with prefix 10uLabs-JobQueue"


def test_job_queue_dlq_exists(sqs_client):
    """Verify the job queue DLQ exists."""
    response = sqs_client.list_queues(QueueNamePrefix="10uLabs-JobQueueDLQ")
    queue_urls = response.get("QueueUrls", [])
    assert len(queue_urls) >= 1, "No job queue DLQ found with prefix 10uLabs-JobQueueDLQ"


def test_webhook_dlq_exists(sqs_client):
    """Verify the webhook DLQ exists."""
    response = sqs_client.list_queues(QueueNamePrefix="10uLabs-WebhookDLQ")
    queue_urls = response.get("QueueUrls", [])
    assert len(queue_urls) >= 1, "No webhook DLQ found with prefix 10uLabs-WebhookDLQ"


def test_drift_recovery_queue_exists(sqs_client):
    """Verify the drift recovery FIFO queue exists."""
    response = sqs_client.list_queues(QueueNamePrefix="10uLabs-DriftRecovery")
    queue_urls = response.get("QueueUrls", [])
    fifo_queues = [q for q in queue_urls if q.endswith(".fifo")]
    assert len(fifo_queues) >= 1, "No drift recovery FIFO queue found"
