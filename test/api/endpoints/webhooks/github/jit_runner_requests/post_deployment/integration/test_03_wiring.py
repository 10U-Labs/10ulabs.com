"""Post-deployment wiring tests for runners endpoint.

Layer 3: Verify all components are connected properly.
These tests run after existence and configuration tests pass.

This includes:
- EventBridge rule targets
- SQS event source mappings
- SQS DLQ wiring
- IAM role attachments and cross-service permissions
"""
import json

import pytest


pytestmark = pytest.mark.layer(3)


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


# === SQS DLQ Wiring ===


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


# === Lambda Role Attachment ===


def test_webhook_handler_uses_correct_role(lambda_client, config):
    """Verify webhook handler Lambda has the correct execution role attached."""
    function_name = config["webhook_handler_function_name"]
    role_name = config["webhook_handler_service_role_name"]
    account_id = config["aws_account_id"]

    response = lambda_client.get_function(FunctionName=function_name)
    actual_role_arn = response["Configuration"]["Role"]
    expected_role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

    assert actual_role_arn == expected_role_arn


# === Role Policy Permissions (Cross-Service Wiring) ===


def _role_has_permission(iam_client, role_name, permission):
    """Check if a role has a specific permission in its inline policies."""
    policies = iam_client.list_role_policies(RoleName=role_name)

    for policy_name in policies["PolicyNames"]:
        policy = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        document = policy["PolicyDocument"]

        for statement in document.get("Statement", []):
            actions = statement.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            if permission in actions:
                return True

    return False


def test_webhook_handler_role_has_sqs_get_queue_attributes(iam_client, config):
    """Verify webhook handler role has GetQueueAttributes permission on job queue.

    The webhook_router.py code calls get_queue_attributes on the job queue
    to publish queue depth metrics after enqueuing jobs.
    """
    role_name = config["webhook_handler_service_role_name"]
    assert _role_has_permission(iam_client, role_name, "sqs:GetQueueAttributes"), (
        f"Role {role_name} missing sqs:GetQueueAttributes permission - "
        "webhook_router.py needs this to publish queue depth metrics"
    )


def test_webhook_handler_role_has_sqs_send_message(iam_client, config):
    """Verify webhook handler role has SendMessage permission."""
    role_name = config["webhook_handler_service_role_name"]
    assert _role_has_permission(iam_client, role_name, "sqs:SendMessage"), (
        f"Role {role_name} missing sqs:SendMessage permission"
    )


def test_webhook_handler_role_has_dynamodb_access(iam_client, config):
    """Verify webhook handler role has DynamoDB access for idempotency."""
    role_name = config["webhook_handler_service_role_name"]
    assert _role_has_permission(iam_client, role_name, "dynamodb:PutItem"), (
        f"Role {role_name} missing dynamodb:PutItem permission"
    )


def test_webhook_handler_role_has_ssm_access(iam_client, config):
    """Verify webhook handler role has SSM access for secrets."""
    role_name = config["webhook_handler_service_role_name"]
    assert _role_has_permission(iam_client, role_name, "ssm:GetParameter"), (
        f"Role {role_name} missing ssm:GetParameter permission"
    )


def test_webhook_handler_role_has_cloudwatch_metrics(iam_client, config):
    """Verify webhook handler role has CloudWatch metrics permission."""
    role_name = config["webhook_handler_service_role_name"]
    assert _role_has_permission(iam_client, role_name, "cloudwatch:PutMetricData"), (
        f"Role {role_name} missing cloudwatch:PutMetricData permission"
    )


# === CloudWatch Logs Subscription Filters → Firehose Wiring ===


def test_runners_handler_subscription_filter_destinations_firehose(
    logs_client, runners_handler_log_group
):
    """Verify runners handler subscription routes to Firehose."""
    log_group = runners_handler_log_group["name"]
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    if response["subscriptionFilters"]:
        destination_arn = response["subscriptionFilters"][0]["destinationArn"]
        assert "firehose" in destination_arn


def test_circuit_breaker_recovery_subscription_filter_destinations_firehose(
    logs_client, circuit_breaker_recovery_log_group
):
    """Verify circuit breaker recovery subscription routes to Firehose."""
    log_group = circuit_breaker_recovery_log_group["name"]
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    if response["subscriptionFilters"]:
        destination_arn = response["subscriptionFilters"][0]["destinationArn"]
        assert "firehose" in destination_arn


def test_circuit_breaker_remediation_subscription_filter_destinations_firehose(
    logs_client, circuit_breaker_remediation_log_group
):
    """Verify circuit breaker remediation subscription routes to Firehose."""
    log_group = circuit_breaker_remediation_log_group["name"]
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    if response["subscriptionFilters"]:
        destination_arn = response["subscriptionFilters"][0]["destinationArn"]
        assert "firehose" in destination_arn


def test_dlq_reprocessor_subscription_filter_destinations_firehose(
    logs_client, dlq_reprocessor_log_group
):
    """Verify DLQ reprocessor subscription routes to Firehose."""
    log_group = dlq_reprocessor_log_group["name"]
    response = logs_client.describe_subscription_filters(logGroupName=log_group)
    if response["subscriptionFilters"]:
        destination_arn = response["subscriptionFilters"][0]["destinationArn"]
        assert "firehose" in destination_arn
