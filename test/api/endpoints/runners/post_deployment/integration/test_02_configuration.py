"""Post-deployment configuration tests for runners endpoint.

Layer 2: Verify all deployed resources are configured correctly.
These tests run after existence tests pass.
"""
import json
import re

import pytest


pytestmark = pytest.mark.layer(2)


# === DynamoDB Table Configuration ===


def test_idempotency_table_has_ttl_enabled(dynamodb_client, config):
    """Verify idempotency table has TTL enabled."""
    table_name = config["idempotency_table_name"]
    response = dynamodb_client.describe_time_to_live(TableName=table_name)
    assert response["TimeToLiveDescription"]["TimeToLiveStatus"] == "ENABLED"


def test_idempotency_table_has_pay_per_request_billing(dynamodb_client, config):
    """Verify idempotency table uses PAY_PER_REQUEST billing mode."""
    table_name = config["idempotency_table_name"]
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response["Table"]["BillingModeSummary"]["BillingMode"] == "PAY_PER_REQUEST"


def test_idempotency_table_has_pitr_enabled(dynamodb_client, config):
    """Verify idempotency table has point-in-time recovery enabled."""
    table_name = config["idempotency_table_name"]
    response = dynamodb_client.describe_continuous_backups(TableName=table_name)
    pitr = response["ContinuousBackupsDescription"]["PointInTimeRecoveryDescription"]
    assert pitr["PointInTimeRecoveryStatus"] == "ENABLED"


def test_idempotency_table_has_request_id_key(dynamodb_client, config):
    """Verify idempotency table has request_id as partition key."""
    table_name = config["idempotency_table_name"]
    response = dynamodb_client.describe_table(TableName=table_name)
    key_schema = response["Table"]["KeySchema"]
    partition_key = next(k for k in key_schema if k["KeyType"] == "HASH")
    assert partition_key["AttributeName"] == "request_id"


def test_incidents_table_has_ttl_enabled(dynamodb_client, config):
    """Verify incidents table has TTL enabled."""
    table_name = f"{config['resource_prefix']}-incidents"
    response = dynamodb_client.describe_time_to_live(TableName=table_name)
    assert response["TimeToLiveDescription"]["TimeToLiveStatus"] == "ENABLED"


def test_incidents_table_has_pay_per_request_billing(dynamodb_client, config):
    """Verify incidents table uses PAY_PER_REQUEST billing mode."""
    table_name = f"{config['resource_prefix']}-incidents"
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response["Table"]["BillingModeSummary"]["BillingMode"] == "PAY_PER_REQUEST"


def test_incidents_table_has_incident_id_key(dynamodb_client, config):
    """Verify incidents table has incident_id as partition key."""
    table_name = f"{config['resource_prefix']}-incidents"
    response = dynamodb_client.describe_table(TableName=table_name)
    key_schema = response["Table"]["KeySchema"]
    assert key_schema[0]["AttributeName"] == "incident_id"


def test_incidents_table_has_pitr_enabled(dynamodb_client, config):
    """Verify incidents table has point-in-time recovery enabled."""
    table_name = f"{config['resource_prefix']}-incidents"
    response = dynamodb_client.describe_continuous_backups(TableName=table_name)
    pitr = response["ContinuousBackupsDescription"]["PointInTimeRecoveryDescription"]
    assert pitr["PointInTimeRecoveryStatus"] == "ENABLED"


def test_circuit_breaker_state_table_has_ttl_enabled(dynamodb_client, config):
    """Verify circuit breaker state table has TTL enabled."""
    table_name = f"{config['resource_prefix']}-circuit-breaker-state"
    response = dynamodb_client.describe_time_to_live(TableName=table_name)
    assert response["TimeToLiveDescription"]["TimeToLiveStatus"] == "ENABLED"


def test_circuit_breaker_state_table_has_pay_per_request_billing(dynamodb_client, config):
    """Verify circuit breaker state table uses PAY_PER_REQUEST billing mode."""
    table_name = f"{config['resource_prefix']}-circuit-breaker-state"
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response["Table"]["BillingModeSummary"]["BillingMode"] == "PAY_PER_REQUEST"


def test_circuit_breaker_state_table_has_state_id_key(dynamodb_client, config):
    """Verify circuit breaker state table has state_id as partition key."""
    table_name = f"{config['resource_prefix']}-circuit-breaker-state"
    response = dynamodb_client.describe_table(TableName=table_name)
    key_schema = response["Table"]["KeySchema"]
    assert key_schema[0]["AttributeName"] == "state_id"


def test_circuit_breaker_state_table_has_pitr_enabled(dynamodb_client, config):
    """Verify circuit breaker state table has point-in-time recovery enabled."""
    table_name = f"{config['resource_prefix']}-circuit-breaker-state"
    response = dynamodb_client.describe_continuous_backups(TableName=table_name)
    pitr = response["ContinuousBackupsDescription"]["PointInTimeRecoveryDescription"]
    assert pitr["PointInTimeRecoveryStatus"] == "ENABLED"


# === SQS Queue Configuration ===


def test_job_queue_has_redrive_policy(sqs_client, config):
    """Verify job queue has redrive policy to DLQ."""
    queue_name = config["job_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["RedrivePolicy"]
    )
    assert "RedrivePolicy" in attributes["Attributes"]


def test_job_queue_has_visibility_timeout(sqs_client, config):
    """Verify job queue has visibility timeout greater than 30 seconds."""
    queue_name = config["job_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["VisibilityTimeout"]
    )
    visibility_timeout = int(attributes["Attributes"]["VisibilityTimeout"])
    assert visibility_timeout > 30


def test_job_queue_is_not_fifo(sqs_client, config):
    """Verify job queue is standard (not FIFO) for webhook processing."""
    queue_name = config["job_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
    assert ".fifo" not in queue_url


def test_job_dlq_has_message_retention(sqs_client, config):
    """Verify job DLQ has message retention configured."""
    queue_name = config["job_dlq_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["MessageRetentionPeriod"]
    )
    retention = int(attributes["Attributes"]["MessageRetentionPeriod"])
    assert retention > 0


def test_webhook_ingress_queue_has_redrive_policy(sqs_client, config):
    """Verify webhook ingress queue has redrive policy to DLQ."""
    queue_name = config["webhook_ingress_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["RedrivePolicy"]
    )
    assert "RedrivePolicy" in attributes["Attributes"]


def test_webhook_ingress_queue_has_short_retention(sqs_client, config):
    """Verify webhook ingress queue has short retention for DDoS protection."""
    queue_name = config["webhook_ingress_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["MessageRetentionPeriod"]
    )
    retention = int(attributes["Attributes"]["MessageRetentionPeriod"])
    # Should be <= 1 hour (3600 seconds) for DDoS protection
    assert retention <= 3600


def test_ignored_events_queue_has_redrive_policy(sqs_client, config):
    """Verify ignored events queue has redrive policy."""
    queue_name = config["ignored_events_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["RedrivePolicy"]
    )
    assert "RedrivePolicy" in attributes["Attributes"]


def test_drift_recovery_queue_is_fifo(sqs_client, config):
    """Verify drift recovery queue is configured as FIFO."""
    queue_name = config["drift_recovery_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["FifoQueue"]
    )
    assert attributes["Attributes"].get("FifoQueue") == "true"


def test_drift_recovery_queue_has_content_deduplication(sqs_client, config):
    """Verify drift recovery queue has content-based deduplication enabled."""
    queue_name = config["drift_recovery_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["ContentBasedDeduplication"]
    )
    assert attributes["Attributes"].get("ContentBasedDeduplication") == "true"


# === EventBridge Rule Configuration ===


def test_circuit_breaker_remediation_rule_enabled(events_client, config):
    """Verify circuit breaker remediation rule is enabled."""
    rule_name = f"{config['resource_prefix']}-circuit-breaker-remediation"
    response = events_client.describe_rule(Name=rule_name)
    assert response["State"] == "ENABLED"


def test_circuit_breaker_remediation_rule_has_cloudwatch_source(events_client, config):
    """Verify circuit breaker remediation rule filters CloudWatch events."""
    rule_name = f"{config['resource_prefix']}-circuit-breaker-remediation"
    response = events_client.describe_rule(Name=rule_name)
    event_pattern = json.loads(response["EventPattern"])
    assert event_pattern["source"] == ["aws.cloudwatch"]


def test_circuit_breaker_remediation_rule_filters_alarm_name(events_client, config):
    """Verify circuit breaker remediation rule filters by alarm name."""
    rule_name = f"{config['resource_prefix']}-circuit-breaker-remediation"
    response = events_client.describe_rule(Name=rule_name)
    event_pattern = json.loads(response["EventPattern"])
    assert "alarmName" in event_pattern["detail"]


def test_circuit_breaker_recovery_rule_enabled(events_client, config):
    """Verify circuit breaker recovery rule is enabled."""
    rule_name = f"{config['resource_prefix']}-circuit-breaker-recovery"
    response = events_client.describe_rule(Name=rule_name)
    assert response["State"] == "ENABLED"


def test_circuit_breaker_recovery_rule_has_5_minute_schedule(events_client, config):
    """Verify circuit breaker recovery rule runs every 5 minutes."""
    rule_name = f"{config['resource_prefix']}-circuit-breaker-recovery"
    response = events_client.describe_rule(Name=rule_name)
    assert response["ScheduleExpression"] == "rate(5 minutes)"


def test_dlq_reprocessor_rule_enabled(events_client, config):
    """Verify DLQ reprocessor rule is enabled."""
    rule_name = f"{config['resource_prefix']}-dlq-reprocessor"
    response = events_client.describe_rule(Name=rule_name)
    assert response["State"] == "ENABLED"


def test_dlq_reprocessor_rule_has_15_minute_schedule(events_client, config):
    """Verify DLQ reprocessor rule runs every 15 minutes."""
    rule_name = f"{config['resource_prefix']}-dlq-reprocessor"
    response = events_client.describe_rule(Name=rule_name)
    assert response["ScheduleExpression"] == "rate(15 minutes)"


# === Resource Naming Conventions ===


def _is_pascalcase(name):
    """Check if name follows PascalCase convention (no dashes, underscores)."""
    return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))


def test_webhook_handler_name_is_pascalcase(lambda_client, config):
    """Verify WebhookHandler uses PascalCase naming."""
    function_name = config["webhook_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    actual_name = response["Configuration"]["FunctionName"]
    assert _is_pascalcase(actual_name), f"Name '{actual_name}' is not PascalCase"


def test_runner_starter_name_is_pascalcase(lambda_client, config):
    """Verify RunnerStarter uses PascalCase naming."""
    function_name = config["runner_starter_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    actual_name = response["Configuration"]["FunctionName"]
    assert _is_pascalcase(actual_name), f"Name '{actual_name}' is not PascalCase"


# === CloudWatch Log Group Configuration ===


def test_circuit_breaker_recovery_log_group_has_retention(
    circuit_breaker_recovery_log_group
):
    """Verify circuit breaker recovery log group has retention configured."""
    assert circuit_breaker_recovery_log_group["retention"] is not None, (
        f"Log group '{circuit_breaker_recovery_log_group['name']}' "
        "has no retention policy"
    )


def test_circuit_breaker_recovery_log_group_retention_is_7_days(
    circuit_breaker_recovery_log_group
):
    """Verify circuit breaker recovery log group retention is 7 days."""
    retention = circuit_breaker_recovery_log_group["retention"]
    assert retention == 7, (
        f"Log group '{circuit_breaker_recovery_log_group['name']}' "
        f"retention is {retention} days, expected 7"
    )


def test_circuit_breaker_remediation_log_group_has_retention(
    circuit_breaker_remediation_log_group
):
    """Verify circuit breaker remediation log group has retention configured."""
    assert circuit_breaker_remediation_log_group["retention"] is not None, (
        f"Log group '{circuit_breaker_remediation_log_group['name']}' "
        "has no retention policy"
    )


def test_circuit_breaker_remediation_log_group_retention_is_7_days(
    circuit_breaker_remediation_log_group
):
    """Verify circuit breaker remediation log group retention is 7 days."""
    retention = circuit_breaker_remediation_log_group["retention"]
    assert retention == 7, (
        f"Log group '{circuit_breaker_remediation_log_group['name']}' "
        f"retention is {retention} days, expected 7"
    )


def test_dlq_reprocessor_log_group_has_retention(dlq_reprocessor_log_group):
    """Verify DLQ reprocessor log group has retention configured."""
    assert dlq_reprocessor_log_group["retention"] is not None, (
        f"Log group '{dlq_reprocessor_log_group['name']}' has no retention policy"
    )


def test_dlq_reprocessor_log_group_retention_is_7_days(dlq_reprocessor_log_group):
    """Verify DLQ reprocessor log group retention is 7 days."""
    retention = dlq_reprocessor_log_group["retention"]
    assert retention == 7, (
        f"Log group '{dlq_reprocessor_log_group['name']}' "
        f"retention is {retention} days, expected 7"
    )


# === CloudWatch Logs Subscription Filter Configuration ===


def test_runners_handler_subscription_filter_name(logs_client, runners_handler_log_group):
    """Verify runners handler subscription filter has correct name."""
    log_group = runners_handler_log_group["name"]
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    filter_names = [f["filterName"] for f in response["subscriptionFilters"]]
    assert "runners-handler-to-firehose" in filter_names


def test_runners_handler_subscription_filter_uses_empty_pattern(
    logs_client, runners_handler_log_group
):
    """Verify runners handler subscription filter captures all logs."""
    log_group = runners_handler_log_group["name"]
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    for sub_filter in response["subscriptionFilters"]:
        if sub_filter["filterName"] == "runners-handler-to-firehose":
            assert sub_filter["filterPattern"] == ""


def test_circuit_breaker_recovery_subscription_filter_name(
    logs_client, circuit_breaker_recovery_log_group
):
    """Verify circuit breaker recovery subscription filter has correct name."""
    log_group = circuit_breaker_recovery_log_group["name"]
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    filter_names = [f["filterName"] for f in response["subscriptionFilters"]]
    assert "circuit-breaker-recovery-to-firehose" in filter_names


def test_circuit_breaker_recovery_subscription_filter_uses_empty_pattern(
    logs_client, circuit_breaker_recovery_log_group
):
    """Verify circuit breaker recovery subscription filter captures all logs."""
    log_group = circuit_breaker_recovery_log_group["name"]
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    for sub_filter in response["subscriptionFilters"]:
        if sub_filter["filterName"] == "circuit-breaker-recovery-to-firehose":
            assert sub_filter["filterPattern"] == ""


def test_circuit_breaker_remediation_subscription_filter_name(
    logs_client, circuit_breaker_remediation_log_group
):
    """Verify circuit breaker remediation subscription filter has correct name."""
    log_group = circuit_breaker_remediation_log_group["name"]
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    filter_names = [f["filterName"] for f in response["subscriptionFilters"]]
    assert "circuit-breaker-remediation-to-firehose" in filter_names


def test_circuit_breaker_remediation_subscription_filter_uses_empty_pattern(
    logs_client, circuit_breaker_remediation_log_group
):
    """Verify circuit breaker remediation subscription filter captures all logs."""
    log_group = circuit_breaker_remediation_log_group["name"]
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    for sub_filter in response["subscriptionFilters"]:
        if sub_filter["filterName"] == "circuit-breaker-remediation-to-firehose":
            assert sub_filter["filterPattern"] == ""


def test_dlq_reprocessor_subscription_filter_name(logs_client, dlq_reprocessor_log_group):
    """Verify DLQ reprocessor subscription filter has correct name."""
    log_group = dlq_reprocessor_log_group["name"]
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    filter_names = [f["filterName"] for f in response["subscriptionFilters"]]
    assert "dlq-reprocessor-to-firehose" in filter_names


def test_dlq_reprocessor_subscription_filter_uses_empty_pattern(
    logs_client, dlq_reprocessor_log_group
):
    """Verify DLQ reprocessor subscription filter captures all logs."""
    log_group = dlq_reprocessor_log_group["name"]
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    for sub_filter in response["subscriptionFilters"]:
        if sub_filter["filterName"] == "dlq-reprocessor-to-firehose":
            assert sub_filter["filterPattern"] == ""
