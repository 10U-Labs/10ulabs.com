"""IAM role test battery for www_shared pre-deployment validation.

Tests are ordered to fail fast with maximum diagnostic granularity:
1. Role existence
2. Trust policy configuration
3. Policy attachment verification
4. Capability verification (can we use the role's permissions)
"""
import pytest
from botocore.exceptions import ClientError


class TestRoleExistence:
    """Layer 1: Verify the IAM role exists."""

    def test_01_can_call_iam_get_role_api(self, iam_client, github_actions_role_name):
        """Verify we have permission to call iam:GetRole."""
        try:
            iam_client.get_role(RoleName=github_actions_role_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail("No permission to call iam:GetRole")
            raise

    def test_02_github_actions_role_exists(self, iam_client, github_actions_role_name):
        """Verify the GitHub Actions IAM role exists."""
        try:
            response = iam_client.get_role(RoleName=github_actions_role_name)
            assert response["Role"]["RoleName"] == github_actions_role_name
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(
                    f"GitHub Actions role '{github_actions_role_name}' does not exist"
                )
            raise


class TestTrustPolicyConfiguration:
    """Layer 2a: Verify the role's trust policy allows GitHub OIDC."""

    def test_01_trust_policy_has_federated_principal(
        self, iam_client, github_actions_role_name, current_identity
    ):
        """Verify trust policy has GitHub OIDC as federated principal."""
        account_id = current_identity["Account"]
        expected_provider = (
            f"arn:aws:iam::{account_id}:oidc-provider/"
            "token.actions.githubusercontent.com"
        )
        response = iam_client.get_role(RoleName=github_actions_role_name)
        trust_policy = response["Role"]["AssumeRolePolicyDocument"]
        statements = trust_policy.get("Statement", [])
        federated_principals = []
        for stmt in statements:
            principal = stmt.get("Principal", {})
            if isinstance(principal, dict):
                federated = principal.get("Federated")
                if federated:
                    if isinstance(federated, list):
                        federated_principals.extend(federated)
                    else:
                        federated_principals.append(federated)
        assert expected_provider in federated_principals, (
            f"Trust policy missing GitHub OIDC provider. "
            f"Expected: {expected_provider}, Found: {federated_principals}"
        )

    def test_02_trust_policy_has_sts_assume_role_action(
        self, iam_client, github_actions_role_name
    ):
        """Verify trust policy allows sts:AssumeRoleWithWebIdentity."""
        response = iam_client.get_role(RoleName=github_actions_role_name)
        trust_policy = response["Role"]["AssumeRolePolicyDocument"]
        statements = trust_policy.get("Statement", [])
        actions = []
        for stmt in statements:
            action = stmt.get("Action", [])
            if isinstance(action, list):
                actions.extend(action)
            else:
                actions.append(action)
        assert "sts:AssumeRoleWithWebIdentity" in actions, (
            "Trust policy missing sts:AssumeRoleWithWebIdentity action"
        )


class TestPolicyAttachmentAndCapability:
    """Layer 2b/3: Verify policy attachment and actual role capability."""

    def test_01_can_list_attached_policies(
        self, iam_client, github_actions_role_name
    ):
        """Verify we have permission to list attached policies."""
        try:
            iam_client.list_attached_role_policies(RoleName=github_actions_role_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail("No permission to call iam:ListAttachedRolePolicies")
            raise

    def test_02_role_has_administrator_access(
        self, iam_client, github_actions_role_name
    ):
        """Verify role has AdministratorAccess policy attached."""
        response = iam_client.list_attached_role_policies(
            RoleName=github_actions_role_name
        )
        policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
        admin_policy = "arn:aws:iam::aws:policy/AdministratorAccess"
        assert admin_policy in policy_arns, (
            f"Role missing AdministratorAccess policy. "
            f"Attached policies: {policy_arns}"
        )

    def test_03_current_identity_uses_expected_role(
        self, current_identity, github_actions_role_arn
    ):
        """Verify current execution context is using the expected role."""
        current_arn = current_identity["Arn"]
        role_name = github_actions_role_arn.split("/")[-1]
        assert role_name in current_arn, (
            f"Current identity ({current_arn}) does not appear to be using "
            f"the expected role ({github_actions_role_arn})"
        )
