"""Tests to validate IAM credentials before runners deployment.

These tests MUST run first (test_01_) because all other tests depend on having
valid AWS credentials and IAM permissions.

Five-layer testing model (Layers 1-2):
- Layer 1: Authentication - Are credentials configured and valid?
- Layer 2: Authorization - Can we call required APIs?
"""

from botocore.exceptions import ClientError, NoCredentialsError
import pytest


class TestAWSCredentialsAuthentication:
    """Layer 1: Verify AWS credentials are available and valid."""

    def test_01_credentials_available(self, sts_client):
        """Verify AWS credentials are configured."""
        try:
            sts_client.get_caller_identity()
        except NoCredentialsError:
            pytest.fail(
                "No AWS credentials found. "
                "Configure credentials via environment variables, "
                "~/.aws/credentials, or IAM role."
            )

    def test_02_can_call_sts_api(self, sts_client):
        """Verify we can call sts:GetCallerIdentity."""
        try:
            response = sts_client.get_caller_identity()
            assert "Account" in response
        except ClientError as e:
            pytest.fail(
                f"Failed to call sts:GetCallerIdentity: "
                f"{e.response['Error']['Message']}. "
                "Check AWS credentials are valid and not expired."
            )

    def test_03_caller_identity_has_arn(self, sts_client):
        """Verify caller identity includes ARN."""
        try:
            response = sts_client.get_caller_identity()
            assert "Arn" in response
        except ClientError as e:
            pytest.fail(
                f"Failed to get caller ARN: {e.response['Error']['Message']}"
            )

    def test_04_caller_identity_is_role(self, caller_identity):
        """Verify we are running as an IAM role (not user)."""
        arn = caller_identity.get("Arn", "")
        assert ":assumed-role/" in arn or ":role/" in arn, (
            f"Expected to be running as IAM role, but running as: {arn}. "
            "GitHub Actions should assume the GitHub Actions OIDC role."
        )


class TestIAMRoleAuthorization:
    """Layer 2: Verify we have permission to call required APIs."""

    def test_01_can_call_iam_get_role_api(self, iam_client, current_role_name):
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

    def test_02_can_call_dynamodb_list_tables_api(self, dynamodb_client):
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

    def test_03_can_call_sqs_list_queues_api(self, sqs_client):
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

    def test_04_can_call_lambda_list_functions_api(self, lambda_client):
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
