"""Integration tests for Lambda KMS policy configuration.

Five-layer testing model:
- Layer 3: Existence - Does the KMS policy exist on the Lambda role?
- Layer 4: Configuration - Does the policy have correct permissions?

These tests verify the deployed Lambda role has the correct IAM permissions
to decrypt environment variables using the AWS-managed Lambda KMS key.

This is a regression test for the KMSAccessDeniedException bug where the
Lambda returned 502 errors because it could not decrypt environment variables.
"""

from botocore.exceptions import ClientError
import pytest


LAMBDA_ROLE_NAME = "TenULabsTroubleshooterOfWorkflowsWebhookRole"
KMS_POLICY_NAME = "TenULabsTroubleshooterOfWorkflowsWebhookKMSPolicy"


class TestKMSPolicyExistence:
    """Layer 3: Verify the KMS policy exists on the Lambda role."""

    def test_01_kms_policy_exists(self, iam_client):
        """Verify the KMS inline policy exists on the Lambda role."""
        try:
            response = iam_client.get_role_policy(
                RoleName=LAMBDA_ROLE_NAME, PolicyName=KMS_POLICY_NAME
            )
            assert response["PolicyName"] == KMS_POLICY_NAME
        except ClientError as err:
            if err.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(
                    f"KMS policy '{KMS_POLICY_NAME}' not found on role "
                    f"'{LAMBDA_ROLE_NAME}'. Lambda needs kms:Decrypt permission "
                    "to decrypt environment variables. "
                    "Run terraform apply in src/api/endpoints/agents/troubleshooter_of_workflows/"
                )
            raise


class TestKMSPolicyConfiguration:
    """Layer 4: Verify the KMS policy has correct permissions."""

    def test_01_kms_policy_has_decrypt_action(self, iam_client):
        """Verify the policy grants kms:Decrypt permission."""
        try:
            response = iam_client.get_role_policy(
                RoleName=LAMBDA_ROLE_NAME, PolicyName=KMS_POLICY_NAME
            )
            policy = response["PolicyDocument"]
            statements = policy.get("Statement", [])

            actions = []
            for stmt in statements:
                stmt_actions = stmt.get("Action", [])
                if isinstance(stmt_actions, str):
                    stmt_actions = [stmt_actions]
                actions.extend(stmt_actions)

            assert "kms:Decrypt" in actions, (
                "kms:Decrypt action not found in KMS policy. "
                "Lambda needs this permission to decrypt environment variables. "
                f"Found actions: {actions}"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip("KMS policy not found")
            raise

    def test_02_kms_policy_has_describe_key_action(self, iam_client):
        """Verify the policy grants kms:DescribeKey permission."""
        try:
            response = iam_client.get_role_policy(
                RoleName=LAMBDA_ROLE_NAME, PolicyName=KMS_POLICY_NAME
            )
            policy = response["PolicyDocument"]
            statements = policy.get("Statement", [])

            actions = []
            for stmt in statements:
                stmt_actions = stmt.get("Action", [])
                if isinstance(stmt_actions, str):
                    stmt_actions = [stmt_actions]
                actions.extend(stmt_actions)

            assert "kms:DescribeKey" in actions, (
                "kms:DescribeKey action not found in KMS policy. "
                "This permission is required alongside kms:Decrypt. "
                f"Found actions: {actions}"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip("KMS policy not found")
            raise

    def test_03_kms_policy_has_allow_effect(self, iam_client):
        """Verify the KMS policy statement has Allow effect."""
        try:
            response = iam_client.get_role_policy(
                RoleName=LAMBDA_ROLE_NAME, PolicyName=KMS_POLICY_NAME
            )
            policy = response["PolicyDocument"]
            statements = policy.get("Statement", [])

            has_allow = any(stmt.get("Effect") == "Allow" for stmt in statements)
            assert has_allow, (
                "KMS policy does not have an Allow statement. "
                "The policy must explicitly allow kms:Decrypt."
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip("KMS policy not found")
            raise

    def test_04_kms_policy_has_resource(self, iam_client):
        """Verify the KMS policy specifies a resource."""
        try:
            response = iam_client.get_role_policy(
                RoleName=LAMBDA_ROLE_NAME, PolicyName=KMS_POLICY_NAME
            )
            policy = response["PolicyDocument"]
            statements = policy.get("Statement", [])

            resources = []
            for stmt in statements:
                stmt_resources = stmt.get("Resource", [])
                if isinstance(stmt_resources, str):
                    stmt_resources = [stmt_resources]
                resources.extend(stmt_resources)

            assert len(resources) > 0, (
                "KMS policy does not specify any resources. "
                "The policy must include the KMS key ARN pattern."
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip("KMS policy not found")
            raise
