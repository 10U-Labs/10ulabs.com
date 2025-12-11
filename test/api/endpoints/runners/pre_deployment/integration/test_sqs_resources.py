"""Tests to validate SQS resources exist for runners."""


def test_job_queue_exists(sqs_client, config):
    """Verify the job queue exists."""
    prefix = config['resource_prefix']
    response = sqs_client.list_queues(QueueNamePrefix=f"{prefix}")
    queue_urls = response.get("QueueUrls", [])
    job_queues = [q for q in queue_urls if "jobs" in q and "dlq" not in q]
    assert len(job_queues) >= 1, f"No job queue found for prefix {prefix}"


def test_job_queue_dlq_exists(sqs_client, config):
    """Verify the job queue DLQ exists."""
    prefix = config['resource_prefix']
    response = sqs_client.list_queues(QueueNamePrefix=f"{prefix}")
    queue_urls = response.get("QueueUrls", [])
    job_dlqs = [q for q in queue_urls if "job-dlq" in q]
    assert len(job_dlqs) >= 1, f"No job queue DLQ found for prefix {prefix}"


def test_webhook_dlq_exists(sqs_client, config):
    """Verify the webhook DLQ exists."""
    prefix = config['resource_prefix']
    response = sqs_client.list_queues(QueueNamePrefix=f"{prefix}")
    queue_urls = response.get("QueueUrls", [])
    webhook_dlqs = [q for q in queue_urls if q.endswith("-dlq") and "job" not in q]
    assert len(webhook_dlqs) >= 1, f"No webhook DLQ found for prefix {prefix}"


def test_drift_recovery_queue_exists(sqs_client, config):
    """Verify the drift recovery FIFO queue exists."""
    prefix = config['resource_prefix']
    response = sqs_client.list_queues(QueueNamePrefix=f"{prefix}-DriftRecovery")
    queue_urls = response.get("QueueUrls", [])
    fifo_queues = [q for q in queue_urls if q.endswith(".fifo")]
    assert len(fifo_queues) >= 1, f"No drift recovery FIFO queue found for prefix {prefix}"
