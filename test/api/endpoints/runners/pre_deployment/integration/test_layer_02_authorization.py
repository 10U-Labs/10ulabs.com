"""Layer 2: Authorization - Do we have permission to call required APIs?

These tests verify IAM permissions before checking resource existence.
If authorization fails, we know it's a permissions issue, not a missing resource.

Five-layer testing model:
- Layer 1: Authentication - Are credentials configured and valid?
- Layer 2: Authorization - Do we have permission to call required APIs? (THIS FILE)
- Layer 3: Existence - Do the required resources exist?
- Layer 4: Configuration - Are resources configured correctly?
- Layer 5: Capability - Can we perform required operations?
"""
from botocore.exceptions import ClientError
import pytest


def test_01_can_call_iam_get_role_api(iam_client, current_role_name):
    """Verify we have permission to call iam:GetRole."""
    if not current_role_name:
        pytest.skip("Could not determine current role name")
    try:
        iam_client.get_role(RoleName=current_role_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail(
                f"No permission to call iam:GetRole on '{current_role_name}'. "
                "The role may lack iam:GetRole permission for itself."
            )
        if e.response["Error"]["Code"] == "NoSuchEntity":
            pytest.fail(f"IAM role '{current_role_name}' does not exist.")
        raise


def test_02_can_call_dynamodb_list_tables_api(dynamodb_client):
    """Verify we have permission to call dynamodb:ListTables."""
    try:
        dynamodb_client.list_tables(Limit=1)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDeniedException":
            pytest.fail(
                "No permission to call dynamodb:ListTables. "
                "Check IAM permissions for DynamoDB access."
            )
        raise


def test_03_can_call_sqs_list_queues_api(sqs_client):
    """Verify we have permission to call sqs:ListQueues."""
    try:
        sqs_client.list_queues(MaxResults=1)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail(
                "No permission to call sqs:ListQueues. "
                "Check IAM permissions for SQS access."
            )
        raise


def test_04_can_call_lambda_list_functions_api(lambda_client):
    """Verify we have permission to call lambda:ListFunctions."""
    try:
        lambda_client.list_functions(MaxItems=1)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDeniedException":
            pytest.fail(
                "No permission to call lambda:ListFunctions. "
                "Check IAM permissions for Lambda access."
            )
        raise


def test_05_can_call_ssm_get_parameter_api(ssm_client, ssm_github_pat_name):
    """Verify we have permission to call ssm:GetParameter."""
    try:
        ssm_client.get_parameter(Name=ssm_github_pat_name, WithDecryption=False)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "AccessDeniedException":
            pytest.fail(
                f"No permission to call GetParameter on '{ssm_github_pat_name}'. "
                "Check IAM permissions for ssm:GetParameter."
            )
        if code == "ParameterNotFound":
            pass  # Parameter doesn't exist, but we have permission - that's OK here
        else:
            raise
