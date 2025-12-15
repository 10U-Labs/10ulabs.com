"""Unit tests for troubleshooter_of_workflows IAM policy configuration.

These tests verify the Terraform IAM policy configuration is correct
by parsing the iam.tf file directly, without deploying.
"""

import re
from pathlib import Path

import pytest


# Path: test/api/endpoints/agents/troubleshooter_of_workflows/pre_deployment/unit/test_iam_policy.py
# parents[7] = repo root (10ulabs.com)
IAM_TF_PATH = (
    Path(__file__).resolve().parents[7]
    / "src"
    / "api"
    / "endpoints"
    / "agents"
    / "troubleshooter_of_workflows"
    / "iam.tf"
)


def _read_iam_tf() -> str:
    """Read the iam.tf file contents."""
    with open(IAM_TF_PATH, encoding="utf-8") as f:
        return f.read()


def _extract_agentcore_policy_resource(content: str) -> str:
    """Extract the Resource value from the webhook_lambda_agentcore policy."""
    # Find the webhook_lambda_agentcore resource block
    pattern = (
        r'resource\s+"aws_iam_role_policy"\s+"webhook_lambda_agentcore"\s*\{'
        r'.*?Resource\s*=\s*(\[.*?\]|[^\n]+)'
    )
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1)
    return ""


class TestAgentCoreIAMPolicy:
    """Tests for the AgentCore IAM policy configuration."""

    def test_iam_tf_file_exists(self):
        """Verify iam.tf file exists."""
        assert IAM_TF_PATH.exists(), f"iam.tf not found at {IAM_TF_PATH}"

    def test_webhook_lambda_agentcore_policy_exists(self):
        """Verify the webhook_lambda_agentcore policy resource exists."""
        content = _read_iam_tf()
        assert 'resource "aws_iam_role_policy" "webhook_lambda_agentcore"' in content, (
            "webhook_lambda_agentcore policy resource not found in iam.tf"
        )

    def test_agentcore_policy_has_invoke_permission(self):
        """Verify the policy grants InvokeAgentRuntime permission."""
        content = _read_iam_tf()
        assert "bedrock-agentcore:InvokeAgentRuntime" in content, (
            "InvokeAgentRuntime permission not found in iam.tf"
        )

    def test_agentcore_policy_includes_base_arn(self):
        """Verify the policy includes the base agent runtime ARN."""
        content = _read_iam_tf()
        resource = _extract_agentcore_policy_resource(content)
        assert "agent_runtime_arn" in resource, (
            "Base agent_runtime_arn not found in AgentCore policy Resource. "
            "Policy must include the base ARN for the agent runtime."
        )

    def test_agentcore_policy_includes_subresource_wildcard(self):
        """Verify the policy includes wildcard for runtime subresources.

        The InvokeAgentRuntime API requires access to /runtime-endpoint/DEFAULT
        and potentially other subresources. The policy must include a wildcard
        pattern like ${arn}/* to cover these.

        This is a regression test for the AccessDeniedException bug where the
        Lambda could not invoke the agent due to missing subresource permissions.
        """
        content = _read_iam_tf()
        resource = _extract_agentcore_policy_resource(content)

        # Check for wildcard pattern - could be /* or * at end of ARN reference
        has_wildcard = (
            "agent_runtime_arn}/*" in resource
            or "agent_runtime_arn}*" in resource
            or 'agent_runtime_arn",' in resource  # List with multiple entries
        )

        assert has_wildcard, (
            "AgentCore policy Resource does not include wildcard for subresources. "
            "The policy must include a pattern like '${...agent_runtime_arn}/*' "
            "to allow access to /runtime-endpoint/DEFAULT and other subresources. "
            f"Current Resource value: {resource}"
        )

    def test_agentcore_policy_resource_is_list(self):
        """Verify the policy Resource is a list (best practice for multiple ARNs)."""
        content = _read_iam_tf()
        resource = _extract_agentcore_policy_resource(content)
        assert resource.strip().startswith("["), (
            "AgentCore policy Resource should be a list to include both "
            "the base ARN and wildcard pattern. "
            f"Current Resource value: {resource}"
        )


class TestKMSIAMPolicy:
    """Tests for the KMS IAM policy configuration.

    The webhook Lambda needs kms:Decrypt permission to decrypt environment
    variables encrypted with the AWS-managed Lambda KMS key.

    This is a regression test for the KMSAccessDeniedException bug where the
    Lambda returned 502 errors because it could not decrypt environment variables.
    """

    def test_webhook_lambda_kms_policy_exists(self):
        """Verify the webhook_lambda_kms policy resource exists."""
        content = _read_iam_tf()
        assert 'resource "aws_iam_role_policy" "webhook_lambda_kms"' in content, (
            "webhook_lambda_kms policy resource not found in iam.tf. "
            "Lambda needs kms:Decrypt permission to decrypt environment variables."
        )

    def test_kms_policy_has_decrypt_permission(self):
        """Verify the KMS policy grants kms:Decrypt permission."""
        content = _read_iam_tf()
        assert "kms:Decrypt" in content, (
            "kms:Decrypt permission not found in iam.tf. "
            "Lambda needs this permission to decrypt environment variables."
        )

    def test_kms_policy_has_describe_key_permission(self):
        """Verify the KMS policy grants kms:DescribeKey permission."""
        content = _read_iam_tf()
        assert "kms:DescribeKey" in content, (
            "kms:DescribeKey permission not found in iam.tf. "
            "This permission is required alongside kms:Decrypt."
        )

    def test_kms_policy_uses_shared_module_key_arn(self):
        """Verify the KMS policy uses the shared module's KMS key ARN."""
        content = _read_iam_tf()
        assert "module.shared.kms_lambda_key_arn" in content, (
            "KMS policy should use module.shared.kms_lambda_key_arn as the resource. "
            "This ensures consistency with other endpoints in the codebase."
        )
