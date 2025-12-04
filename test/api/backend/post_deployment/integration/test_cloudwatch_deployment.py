"""Tests for CloudWatch and EventBridge deployment configuration."""


def test_cloudwatch_metrics_namespace_exists(cloudwatch_client):
    """Verify WebhookRouter metrics namespace exists."""
    response = cloudwatch_client.list_metrics(Namespace='WebhookRouter')
    has_metrics = 'Metrics' in response
    assert has_metrics


def test_eventbridge_rule_for_circuit_breaker_remediation_exists(events_client, config):
    """Verify circuit breaker remediation EventBridge rule exists."""
    rules = events_client.list_rules()
    rule_names = [r['Name'] for r in rules['Rules']]
    remediation_rule_name = f"{config['resource_prefix']}-circuit-breaker-remediation"
    rule_exists = remediation_rule_name in rule_names
    assert rule_exists


def test_eventbridge_rule_for_circuit_breaker_recovery_exists(events_client, config):
    """Verify circuit breaker recovery EventBridge rule exists."""
    rules = events_client.list_rules()
    rule_names = [r['Name'] for r in rules['Rules']]
    recovery_rule_name = f"{config['resource_prefix']}-circuit-breaker-recovery"
    rule_exists = recovery_rule_name in rule_names
    assert rule_exists


def test_eventbridge_rule_for_dlq_reprocessor_exists(events_client, config):
    """Verify DLQ reprocessor EventBridge rule exists."""
    rules = events_client.list_rules()
    rule_names = [r['Name'] for r in rules['Rules']]
    dlq_rule_name = f"{config['resource_prefix']}-dlq-reprocessor"
    rule_exists = dlq_rule_name in rule_names
    assert rule_exists


def test_cloudwatch_alarm_circuit_breaker_open_exists(cloudwatch_client, config):
    """Verify circuit breaker open alarm exists."""
    alarm_name = f"{config['resource_prefix']}-circuit-breaker-open"
    alarms = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
    has_one_alarm = len(alarms['MetricAlarms']) == 1
    assert has_one_alarm


def test_cloudwatch_alarm_webhook_handler_errors_exists(cloudwatch_client, config):
    """Verify webhook handler errors alarm exists."""
    alarm_name = f"{config['resource_prefix']}-webhook-handler-errors"
    alarms = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
    has_one_alarm = len(alarms['MetricAlarms']) == 1
    assert has_one_alarm


def test_cloudwatch_alarm_job_queue_dlq_messages_exists(cloudwatch_client, config):
    """Verify job queue DLQ messages alarm exists."""
    alarm_name = f"{config['resource_prefix']}-job-queue-dlq-messages"
    alarms = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
    has_one_alarm = len(alarms['MetricAlarms']) == 1
    assert has_one_alarm
