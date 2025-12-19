"""Post-deployment wiring tests for runners endpoint.

Layer 3: Verify all components are connected properly.
These tests run after existence and configuration tests pass.
"""
import json


# === EventBridge Rule Targets ===


def test_circuit_breaker_remediation_rule_has_target(events_client, config):
    """Verify circuit breaker remediation rule has a Lambda target."""
    rule_name = f"{config['resource_prefix']}-circuit-breaker-remediation"
    targets = events_client.list_targets_by_rule(Rule=rule_name)
    assert len(targets["Targets"]) == 1


def test_circuit_breaker_recovery_rule_has_target(events_client, config):
    """Verify circuit breaker recovery rule has a Lambda target."""
    rule_name = f"{config['resource_prefix']}-circuit-breaker-recovery"
    targets = events_client.list_targets_by_rule(Rule=rule_name)
    assert len(targets["Targets"]) == 1


def test_dlq_reprocessor_rule_has_target(events_client, config):
    """Verify DLQ reprocessor rule has a Lambda target."""
    rule_name = f"{config['resource_prefix']}-dlq-reprocessor"
    targets = events_client.list_targets_by_rule(Rule=rule_name)
    assert len(targets["Targets"]) == 1


# === SQS Event Source Mappings ===


def test_runner_starter_has_event_source_mapping(lambda_client, config):
    """Verify RunnerStarter has an SQS event source mapping."""
    function_name = config["runner_starter_function_name"]
    response = lambda_client.list_event_source_mappings(
        FunctionName=function_name
    )
    assert len(response["EventSourceMappings"]) > 0


def test_runner_starter_triggered_by_job_queue(lambda_client, config):
    """Verify RunnerStarter is triggered by the job queue."""
    function_name = config["runner_starter_function_name"]
    response = lambda_client.list_event_source_mappings(
        FunctionName=function_name
    )
    event_sources = [m["EventSourceArn"] for m in response["EventSourceMappings"]]
    job_queue_name = config["job_queue_name"]
    assert any(job_queue_name in arn for arn in event_sources)


# === SQS DLQ Wiring ===


def test_job_queue_redrive_targets_job_dlq(sqs_client, config):
    """Verify job queue's redrive policy targets job DLQ."""
    job_queue_url = sqs_client.get_queue_url(
        QueueName=config["job_queue_name"]
    )["QueueUrl"]
    job_dlq_url = sqs_client.get_queue_url(
        QueueName=config["job_dlq_name"]
    )["QueueUrl"]

    # Get job queue's redrive policy
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=job_queue_url, AttributeNames=["RedrivePolicy"]
    )
    redrive_policy = json.loads(attributes["Attributes"]["RedrivePolicy"])

    # Get job DLQ ARN
    dlq_attributes = sqs_client.get_queue_attributes(
        QueueUrl=job_dlq_url, AttributeNames=["QueueArn"]
    )
    job_dlq_arn = dlq_attributes["Attributes"]["QueueArn"]

    assert redrive_policy["deadLetterTargetArn"] == job_dlq_arn


def test_webhook_ingress_queue_redrive_targets_dlq(sqs_client, config):
    """Verify webhook ingress queue's redrive policy targets its DLQ."""
    queue_url = sqs_client.get_queue_url(
        QueueName=config["webhook_ingress_queue_name"]
    )["QueueUrl"]
    dlq_url = sqs_client.get_queue_url(
        QueueName=config["webhook_ingress_dlq_name"]
    )["QueueUrl"]

    # Get queue's redrive policy
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["RedrivePolicy"]
    )
    redrive_policy = json.loads(attributes["Attributes"]["RedrivePolicy"])

    # Get DLQ ARN
    dlq_attributes = sqs_client.get_queue_attributes(
        QueueUrl=dlq_url, AttributeNames=["QueueArn"]
    )
    dlq_arn = dlq_attributes["Attributes"]["QueueArn"]

    assert redrive_policy["deadLetterTargetArn"] == dlq_arn
