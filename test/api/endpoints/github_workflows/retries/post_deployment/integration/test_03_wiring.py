"""Post-deployment wiring tests for github_workflows/retries endpoint.

Layer 3: Verify all components are connected properly.
These tests run after existence and configuration tests pass.

This includes:
- Lambda event source mapping to SQS
- SQS DLQ wiring
- IAM role attachments and cross-service permissions
"""
import json

from test_utils.aws_assertions import role_has_permission


# === Lambda Event Source Mapping ===


def test_lambda_has_sqs_event_source_mapping(lambda_client, config):
    """Verify Lambda has an event source mapping to SQS."""
    function_name = config["function_name"]
    response = lambda_client.list_event_source_mappings(FunctionName=function_name)
    mappings = response.get("EventSourceMappings", [])
    sqs_mappings = [m for m in mappings if "sqs" in m.get("EventSourceArn", "")]
    assert len(sqs_mappings) == 1


def test_lambda_event_source_mapping_batch_size_is_1(lambda_client, config):
    """Verify Lambda event source mapping has batch size of 1."""
    function_name = config["function_name"]
    response = lambda_client.list_event_source_mappings(FunctionName=function_name)
    mappings = response.get("EventSourceMappings", [])
    sqs_mappings = [m for m in mappings if "sqs" in m.get("EventSourceArn", "")]
    assert sqs_mappings[0]["BatchSize"] == 1


def test_lambda_event_source_mapping_is_enabled(lambda_client, config):
    """Verify Lambda event source mapping is enabled."""
    function_name = config["function_name"]
    response = lambda_client.list_event_source_mappings(FunctionName=function_name)
    mappings = response.get("EventSourceMappings", [])
    sqs_mappings = [m for m in mappings if "sqs" in m.get("EventSourceArn", "")]
    assert sqs_mappings[0]["State"] == "Enabled"


# === SQS DLQ Wiring ===


def test_main_queue_redrive_targets_dlq(sqs_client, config):
    """Verify main queue's redrive policy targets its DLQ."""
    queue_url = sqs_client.get_queue_url(QueueName=config["queue_name"])["QueueUrl"]
    dlq_arn = sqs_client.get_queue_attributes(
        QueueUrl=sqs_client.get_queue_url(QueueName=config["dlq_name"])["QueueUrl"],
        AttributeNames=["QueueArn"]
    )["Attributes"]["QueueArn"]
    redrive_policy = json.loads(sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["RedrivePolicy"]
    )["Attributes"]["RedrivePolicy"])
    assert redrive_policy["deadLetterTargetArn"] == dlq_arn


def test_main_queue_redrive_max_receive_count_is_3(sqs_client, config):
    """Verify main queue's max receive count is 3."""
    queue_url = sqs_client.get_queue_url(QueueName=config["queue_name"])["QueueUrl"]
    redrive_policy = json.loads(sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["RedrivePolicy"]
    )["Attributes"]["RedrivePolicy"])
    assert redrive_policy["maxReceiveCount"] == 3


# === Lambda Role Attachment ===


def test_lambda_uses_correct_role(lambda_client, config):
    """Verify Lambda has the correct execution role attached."""
    function_name = config["function_name"]
    role_name = config["lambda_role_name"]
    account_id = config["aws_account_id"]
    response = lambda_client.get_function(FunctionName=function_name)
    expected_role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    assert response["Configuration"]["Role"] == expected_role_arn


# === Role Policy Permissions (Cross-Service Wiring) ===


def test_lambda_role_has_ssm_get_parameter(iam_client, config):
    """Verify Lambda role has SSM GetParameter permission for GitHub token."""
    role_name = config["lambda_role_name"]
    assert role_has_permission(iam_client, role_name, "ssm:GetParameter")


def test_lambda_role_has_kms_decrypt(iam_client, config):
    """Verify Lambda role has KMS Decrypt permission for encrypted parameters."""
    role_name = config["lambda_role_name"]
    assert role_has_permission(iam_client, role_name, "kms:Decrypt")


def test_lambda_role_has_sqs_receive_message(iam_client, config):
    """Verify Lambda role has SQS ReceiveMessage permission."""
    role_name = config["lambda_role_name"]
    assert role_has_permission(iam_client, role_name, "sqs:ReceiveMessage")


def test_lambda_role_has_sqs_delete_message(iam_client, config):
    """Verify Lambda role has SQS DeleteMessage permission."""
    role_name = config["lambda_role_name"]
    assert role_has_permission(iam_client, role_name, "sqs:DeleteMessage")


def test_lambda_role_has_sqs_get_queue_attributes(iam_client, config):
    """Verify Lambda role has SQS GetQueueAttributes permission."""
    role_name = config["lambda_role_name"]
    assert role_has_permission(iam_client, role_name, "sqs:GetQueueAttributes")
