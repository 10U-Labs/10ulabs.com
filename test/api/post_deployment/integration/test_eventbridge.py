import json


def test_eventbridge_circuit_breaker_remediation_rule_exists(events_client, config):
    rule_name = f"{config['resource_prefix']}-circuit-breaker-remediation"
    response = events_client.describe_rule(Name=rule_name)
    assert response['Name'] == rule_name


def test_eventbridge_circuit_breaker_remediation_rule_has_target(events_client, config):
    rule_name = f"{config['resource_prefix']}-circuit-breaker-remediation"
    targets = events_client.list_targets_by_rule(Rule=rule_name)
    assert len(targets['Targets']) == 1


def test_eventbridge_circuit_breaker_remediation_event_pattern(events_client, config):
    rule_name = f"{config['resource_prefix']}-circuit-breaker-remediation"
    response = events_client.describe_rule(Name=rule_name)
    event_pattern = json.loads(response['EventPattern'])
    assert event_pattern['source'] == ['aws.cloudwatch']


def test_eventbridge_circuit_breaker_remediation_alarm_filter(events_client, config):
    rule_name = f"{config['resource_prefix']}-circuit-breaker-remediation"
    response = events_client.describe_rule(Name=rule_name)
    event_pattern = json.loads(response['EventPattern'])
    assert 'alarmName' in event_pattern['detail']


def test_eventbridge_circuit_breaker_recovery_rule_exists(events_client, config):
    rule_name = f"{config['resource_prefix']}-circuit-breaker-recovery"
    response = events_client.describe_rule(Name=rule_name)
    assert response['Name'] == rule_name


def test_eventbridge_circuit_breaker_recovery_schedule(events_client, config):
    rule_name = f"{config['resource_prefix']}-circuit-breaker-recovery"
    response = events_client.describe_rule(Name=rule_name)
    assert response['ScheduleExpression'] == 'rate(5 minutes)'


def test_eventbridge_circuit_breaker_recovery_rule_has_target(events_client, config):
    rule_name = f"{config['resource_prefix']}-circuit-breaker-recovery"
    targets = events_client.list_targets_by_rule(Rule=rule_name)
    assert len(targets['Targets']) == 1


def test_eventbridge_circuit_breaker_recovery_state_enabled(events_client, config):
    rule_name = f"{config['resource_prefix']}-circuit-breaker-recovery"
    response = events_client.describe_rule(Name=rule_name)
    assert response['State'] == 'ENABLED'


def test_eventbridge_dlq_reprocessor_rule_exists(events_client, config):
    rule_name = f"{config['resource_prefix']}-dlq-reprocessor"
    response = events_client.describe_rule(Name=rule_name)
    assert response['Name'] == rule_name


def test_eventbridge_dlq_reprocessor_rule_schedule(events_client, config):
    rule_name = f"{config['resource_prefix']}-dlq-reprocessor"
    response = events_client.describe_rule(Name=rule_name)
    assert response['ScheduleExpression'] == 'rate(15 minutes)'


def test_eventbridge_dlq_reprocessor_rule_has_target(events_client, config):
    rule_name = f"{config['resource_prefix']}-dlq-reprocessor"
    targets = events_client.list_targets_by_rule(Rule=rule_name)
    assert len(targets['Targets']) == 1


def test_eventbridge_dlq_reprocessor_state_enabled(events_client, config):
    rule_name = f"{config['resource_prefix']}-dlq-reprocessor"
    response = events_client.describe_rule(Name=rule_name)
    assert response['State'] == 'ENABLED'
