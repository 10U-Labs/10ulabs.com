"""Post-deployment wiring tests for github_workflows/retries endpoint.

Layer 3: Verify all components are connected properly.
These tests run after existence and configuration tests pass.

This includes:
- IAM role attachments and cross-service permissions
"""
from test_utils.aws_assertions import role_has_permission


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
