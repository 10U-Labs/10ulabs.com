def test_cloudwatch_log_group_webhook_handler_exists(logs_client, config):
    log_group_name = config["webhook_handler_log_group_name"]
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    log_groups = [lg for lg in response['logGroups'] if lg['logGroupName'] == log_group_name]
    assert len(log_groups) == 1


def test_cloudwatch_metrics_namespace_exists(cloudwatch_client):
    response = cloudwatch_client.list_metrics(Namespace='WebhookRouter')
    assert 'Metrics' in response


def test_cloudwatch_log_stream_can_be_created(logs_client, config):
    log_group_name = config["webhook_handler_log_group_name"]
    response = logs_client.describe_log_streams(logGroupName=log_group_name, limit=1)
    assert 'logStreams' in response


def test_eventbridge_rule_for_circuit_breaker_remediation_exists(events_client, config):
    rules = events_client.list_rules()
    rule_names = [r['Name'] for r in rules['Rules']]
    remediation_rule_name = f"{config['resource_prefix']}-circuit-breaker-remediation"
    assert remediation_rule_name in rule_names


def test_eventbridge_rule_for_circuit_breaker_recovery_exists(events_client, config):
    rules = events_client.list_rules()
    rule_names = [r['Name'] for r in rules['Rules']]
    recovery_rule_name = f"{config['resource_prefix']}-circuit-breaker-recovery"
    assert recovery_rule_name in rule_names


def test_eventbridge_rule_for_dlq_reprocessor_exists(events_client, config):
    rules = events_client.list_rules()
    rule_names = [r['Name'] for r in rules['Rules']]
    dlq_rule_name = f"{config['resource_prefix']}-dlq-reprocessor"
    assert dlq_rule_name in rule_names


def test_cloudwatch_alarm_circuit_breaker_open_exists(cloudwatch_client, config):
    alarm_name = f"{config['resource_prefix']}-circuit-breaker-open"
    alarms = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
    assert len(alarms['MetricAlarms']) == 1


def test_cloudwatch_alarm_webhook_handler_errors_exists(cloudwatch_client, config):
    alarm_name = f"{config['resource_prefix']}-webhook-handler-errors"
    alarms = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
    assert len(alarms['MetricAlarms']) == 1


def test_cloudwatch_alarm_job_queue_dlq_messages_exists(cloudwatch_client, config):
    alarm_name = f"{config['resource_prefix']}-job-queue-dlq-messages"
    alarms = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
    assert len(alarms['MetricAlarms']) == 1


def test_cloudwatch_log_retention_configured(logs_client, config):
    log_group_name = config["webhook_handler_log_group_name"]
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    assert len(response['logGroups']) > 0
