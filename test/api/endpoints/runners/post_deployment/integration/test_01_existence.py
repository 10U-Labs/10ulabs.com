"""Post-deployment existence tests for runners endpoint.

Layer 1: Verify all deployed resources exist.
These tests run first to catch deployment failures before checking configuration.
"""
from test.api.endpoints.runners.conftest import find_sns_topic_arns

# === Lambda Functions ===


def test_webhook_handler_lambda_exists(lambda_client, config):
    """Verify WebhookHandler Lambda exists."""
    function_name = config["webhook_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_runner_starter_lambda_exists(lambda_client, config):
    """Verify RunnerStarter Lambda exists."""
    function_name = config["runner_starter_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_circuit_breaker_remediation_lambda_exists(lambda_client, config):
    """Verify CircuitBreakerRemediation Lambda exists."""
    function_name = config["circuit_breaker_remediation_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_circuit_breaker_recovery_lambda_exists(lambda_client, config):
    """Verify CircuitBreakerRecovery Lambda exists."""
    function_name = config["circuit_breaker_recovery_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_dlq_reprocessor_lambda_exists(lambda_client, config):
    """Verify DLQReprocessor Lambda exists."""
    function_name = config["dlq_reprocessor_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


# === DynamoDB Tables ===


def test_idempotency_table_exists(dynamodb_client, config):
    """Verify idempotency DynamoDB table exists."""
    table_name = config["idempotency_table_name"]
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response["Table"]["TableName"] == table_name


def test_incidents_table_exists(dynamodb_client, config):
    """Verify incidents DynamoDB table exists."""
    table_name = f"{config['resource_prefix']}-incidents"
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response["Table"]["TableName"] == table_name


def test_circuit_breaker_state_table_exists(dynamodb_client, config):
    """Verify circuit breaker state DynamoDB table exists."""
    table_name = f"{config['resource_prefix']}-circuit-breaker-state"
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response["Table"]["TableName"] == table_name


# === SQS Queues ===


def test_job_queue_exists(sqs_client, config):
    """Verify job queue exists."""
    queue_name = config["job_queue_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert "QueueUrl" in response


def test_job_dlq_exists(sqs_client, config):
    """Verify job DLQ exists."""
    queue_name = config["job_dlq_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert "QueueUrl" in response


def test_webhook_dlq_exists(sqs_client, config):
    """Verify webhook DLQ exists."""
    queue_name = config["webhook_dlq_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert "QueueUrl" in response


def test_webhook_ingress_queue_exists(sqs_client, config):
    """Verify webhook ingress queue exists."""
    queue_name = config["webhook_ingress_queue_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert "QueueUrl" in response


def test_webhook_ingress_dlq_exists(sqs_client, config):
    """Verify webhook ingress DLQ exists."""
    queue_name = config["webhook_ingress_dlq_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert "QueueUrl" in response


def test_ignored_events_queue_exists(sqs_client, config):
    """Verify ignored events queue exists."""
    queue_name = config["ignored_events_queue_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert "QueueUrl" in response


def test_ignored_events_dlq_exists(sqs_client, config):
    """Verify ignored events DLQ exists."""
    queue_name = config["ignored_events_dlq_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert "QueueUrl" in response


def test_drift_recovery_queue_exists(sqs_client, config):
    """Verify drift recovery FIFO queue exists."""
    queue_name = config["drift_recovery_queue_name"]
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert "QueueUrl" in response


# === EventBridge Rules ===


def test_circuit_breaker_remediation_rule_exists(events_client, config):
    """Verify circuit breaker remediation EventBridge rule exists."""
    rule_name = f"{config['resource_prefix']}-circuit-breaker-remediation"
    response = events_client.describe_rule(Name=rule_name)
    assert response["Name"] == rule_name


def test_circuit_breaker_recovery_rule_exists(events_client, config):
    """Verify circuit breaker recovery EventBridge rule exists."""
    rule_name = f"{config['resource_prefix']}-circuit-breaker-recovery"
    response = events_client.describe_rule(Name=rule_name)
    assert response["Name"] == rule_name


def test_dlq_reprocessor_rule_exists(events_client, config):
    """Verify DLQ reprocessor EventBridge rule exists."""
    rule_name = f"{config['resource_prefix']}-dlq-reprocessor"
    response = events_client.describe_rule(Name=rule_name)
    assert response["Name"] == rule_name


# === CloudWatch Alarms ===


def test_circuit_breaker_open_alarm_exists(cloudwatch_client, config):
    """Verify circuit breaker open CloudWatch alarm exists."""
    alarm_name = f"{config['resource_prefix']}-circuit-breaker-open"
    alarms = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
    assert len(alarms["MetricAlarms"]) == 1


# === SNS Topics ===


def test_circuit_breaker_alerts_topic_exists(sns_client, config):
    """Verify circuit breaker alerts SNS topic exists."""
    topic_name = f"{config['resource_prefix']}-circuit-breaker-alerts"
    matching_topics = find_sns_topic_arns(sns_client, topic_name)
    assert len(matching_topics) == 1


# === CloudWatch Log Groups ===


def test_circuit_breaker_recovery_log_group_exists(logs_client, config):
    """Verify CircuitBreakerRecovery Lambda log group exists."""
    function_name = config["circuit_breaker_recovery_function_name"]
    log_group_name = f"/aws/lambda/{function_name}"
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    log_groups = [
        lg for lg in response["logGroups"] if lg["logGroupName"] == log_group_name
    ]
    assert len(log_groups) == 1


def test_circuit_breaker_remediation_log_group_exists(logs_client, config):
    """Verify CircuitBreakerRemediation Lambda log group exists."""
    function_name = config["circuit_breaker_remediation_function_name"]
    log_group_name = f"/aws/lambda/{function_name}"
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    log_groups = [
        lg for lg in response["logGroups"] if lg["logGroupName"] == log_group_name
    ]
    assert len(log_groups) == 1


def test_dlq_reprocessor_log_group_exists(logs_client, config):
    """Verify DLQReprocessor Lambda log group exists."""
    function_name = config["dlq_reprocessor_function_name"]
    log_group_name = f"/aws/lambda/{function_name}"
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    log_groups = [
        lg for lg in response["logGroups"] if lg["logGroupName"] == log_group_name
    ]
    assert len(log_groups) == 1
