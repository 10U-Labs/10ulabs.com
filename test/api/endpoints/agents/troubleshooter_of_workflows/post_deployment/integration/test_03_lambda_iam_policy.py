"""Integration tests for Lambda IAM policy configuration.

Five-layer testing model:
- Layer 1: Authentication - Covered by test_01_agentcore_runtime.py
- Layer 2: Authorization - Can we call IAM APIs?
- Layer 3: Existence - Does the Lambda role exist?
- Layer 4: Configuration - Does the role have correct policy for AgentCore?

These tests verify the deployed Lambda role has the correct IAM permissions
to invoke the AgentCore agent runtime, including subresource access.
"""

from botocore.exceptions import ClientError
import pytest


LAMBDA_ROLE_NAME = "TenULabsTroubleshooterOfWorkflowsWebhookRole"
AGENTCORE_POLICY_NAME = "TenULabsTroubleshooterOfWorkflowsWebhookAgentCorePolicy"


class TestIAMAPIAuthorization:
    """Layer 2: Verify we can call IAM APIs."""

    def test_01_can_call_get_role_api(self, iam_client):
        """Verify we have permission to call iam:GetRole."""
        try:
            # Use a role we know exists (or will fail with NoSuchEntity, not AccessDenied)
            iam_client.get_role(RoleName=LAMBDA_ROLE_NAME)
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    "No permission to call iam:GetRole. "
                    "Check IAM permissions for iam:GetRole."
                )
            if err.response["Error"]["Code"] == "NoSuchEntity":
                pass  # Role doesn't exist yet, but we have permission to check
            else:
                raise

    def test_02_can_call_get_role_policy_api(self, iam_client):
        """Verify we have permission to call iam:GetRolePolicy."""
        try:
            iam_client.get_role_policy(
                RoleName=LAMBDA_ROLE_NAME, PolicyName=AGENTCORE_POLICY_NAME
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    "No permission to call iam:GetRolePolicy. "
                    "Check IAM permissions for iam:GetRolePolicy."
                )
            if err.response["Error"]["Code"] == "NoSuchEntity":
                pass  # Role/policy doesn't exist yet, but we have permission to check
            else:
                raise


class TestLambdaRoleExistence:
    """Layer 3: Verify the Lambda IAM role exists."""

    def test_01_lambda_role_exists(self, iam_client):
        """Verify the Lambda webhook role exists."""
        try:
            response = iam_client.get_role(RoleName=LAMBDA_ROLE_NAME)
            assert response["Role"]["RoleName"] == LAMBDA_ROLE_NAME
        except ClientError as err:
            if err.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(
                    f"Lambda role '{LAMBDA_ROLE_NAME}' does not exist. "
                    "Run terraform apply in src/api/endpoints/agents/troubleshooter_of_workflows/"
                )
            raise


class TestLambdaRoleConfiguration:
    """Layer 4: Verify the Lambda role has correct AgentCore policy."""

    def test_01_agentcore_policy_exists(self, iam_client):
        """Verify the AgentCore inline policy exists on the Lambda role."""
        try:
            response = iam_client.get_role_policy(
                RoleName=LAMBDA_ROLE_NAME, PolicyName=AGENTCORE_POLICY_NAME
            )
            assert response["PolicyName"] == AGENTCORE_POLICY_NAME
        except ClientError as err:
            if err.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(
                    f"AgentCore policy '{AGENTCORE_POLICY_NAME}' not found on role "
                    f"'{LAMBDA_ROLE_NAME}'. Run terraform apply in src/api/endpoints/agents/troubleshooter_of_workflows/"
                )
            raise

    def test_02_agentcore_policy_has_invoke_action(self, iam_client):
        """Verify the policy grants InvokeAgentRuntime permission."""
        try:
            response = iam_client.get_role_policy(
                RoleName=LAMBDA_ROLE_NAME, PolicyName=AGENTCORE_POLICY_NAME
            )
            policy = response["PolicyDocument"]
            statements = policy.get("Statement", [])

            actions = []
            for stmt in statements:
                stmt_actions = stmt.get("Action", [])
                if isinstance(stmt_actions, str):
                    stmt_actions = [stmt_actions]
                actions.extend(stmt_actions)

            assert "bedrock-agentcore:InvokeAgentRuntime" in actions, (
                "InvokeAgentRuntime action not found in AgentCore policy. "
                f"Found actions: {actions}"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip("AgentCore policy not found")
            raise

    def test_03_agentcore_policy_resource_includes_subresources(self, iam_client):
        """Verify the policy resource includes wildcard for subresources.

        The InvokeAgentRuntime API targets /runtime-endpoint/DEFAULT which
        requires the IAM policy to include this subresource path.

        This is a regression test for the AccessDeniedException bug where
        the Lambda could not invoke the agent because the policy only
        included the base runtime ARN without the /runtime-endpoint/* suffix.
        """
        try:
            response = iam_client.get_role_policy(
                RoleName=LAMBDA_ROLE_NAME, PolicyName=AGENTCORE_POLICY_NAME
            )
            policy = response["PolicyDocument"]
            statements = policy.get("Statement", [])

            resources = []
            for stmt in statements:
                stmt_resources = stmt.get("Resource", [])
                if isinstance(stmt_resources, str):
                    stmt_resources = [stmt_resources]
                resources.extend(stmt_resources)

            # Check that at least one resource includes wildcard for subresources
            has_wildcard = any(
                res.endswith("/*") or res.endswith("*") for res in resources
            )

            assert has_wildcard, (
                "AgentCore policy does not include wildcard for subresources. "
                "The policy must include a resource pattern ending in /* or * "
                "to allow access to /runtime-endpoint/DEFAULT. "
                f"Current resources: {resources}"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip("AgentCore policy not found")
            raise

    def test_04_agentcore_policy_has_at_least_two_resources(self, iam_client):
        """Verify the policy has at least two resources."""
        try:
            response = iam_client.get_role_policy(
                RoleName=LAMBDA_ROLE_NAME, PolicyName=AGENTCORE_POLICY_NAME
            )
            policy = response["PolicyDocument"]
            statements = policy.get("Statement", [])

            resources = []
            for stmt in statements:
                stmt_resources = stmt.get("Resource", [])
                if isinstance(stmt_resources, str):
                    stmt_resources = [stmt_resources]
                resources.extend(stmt_resources)

            assert len(resources) >= 2, (
                "AgentCore policy should have at least 2 resources: "
                "the base runtime ARN and a wildcard pattern for subresources. "
                f"Found {len(resources)} resource(s): {resources}"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip("AgentCore policy not found")
            raise

    def test_05_agentcore_policy_has_base_arn(self, iam_client):
        """Verify the policy includes a base ARN without wildcard."""
        try:
            response = iam_client.get_role_policy(
                RoleName=LAMBDA_ROLE_NAME, PolicyName=AGENTCORE_POLICY_NAME
            )
            policy = response["PolicyDocument"]
            statements = policy.get("Statement", [])

            resources = []
            for stmt in statements:
                stmt_resources = stmt.get("Resource", [])
                if isinstance(stmt_resources, str):
                    stmt_resources = [stmt_resources]
                resources.extend(stmt_resources)

            has_base = any(
                not res.endswith("/*") and not res.endswith("*") for res in resources
            )
            assert has_base, (
                "AgentCore policy must include the base runtime ARN "
                "(without wildcard suffix). "
                f"Resources: {resources}"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip("AgentCore policy not found")
            raise

    def test_06_agentcore_policy_has_wildcard_pattern(self, iam_client):
        """Verify the policy includes a wildcard pattern for subresources."""
        try:
            response = iam_client.get_role_policy(
                RoleName=LAMBDA_ROLE_NAME, PolicyName=AGENTCORE_POLICY_NAME
            )
            policy = response["PolicyDocument"]
            statements = policy.get("Statement", [])

            resources = []
            for stmt in statements:
                stmt_resources = stmt.get("Resource", [])
                if isinstance(stmt_resources, str):
                    stmt_resources = [stmt_resources]
                resources.extend(stmt_resources)

            has_wildcard = any(
                res.endswith("/*") or res.endswith("*") for res in resources
            )
            assert has_wildcard, (
                "AgentCore policy must include a wildcard pattern for subresources "
                "(ending in /* or *). "
                f"Resources: {resources}"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip("AgentCore policy not found")
            raise
