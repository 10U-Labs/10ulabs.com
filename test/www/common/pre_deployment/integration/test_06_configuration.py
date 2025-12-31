"""Layer 6: Configuration tests for www_common pre-deployment validation.

Verify prerequisite resources are configured correctly. Assumes existence tests passed.
"""
import os

import pytest

pytestmark = pytest.mark.layer(6)


def _is_github_actions():
    """Check if running in GitHub Actions."""
    return os.environ.get("GITHUB_ACTIONS") == "true"


def test_trust_policy_has_github_oidc_principal(
    iam_client, github_actions_role_name, current_identity
):
    """Verify trust policy has GitHub OIDC as federated principal."""
    account_id = current_identity["Account"]
    expected_provider = (
        f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
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


def test_trust_policy_has_sts_assume_role_action(iam_client, github_actions_role_name):
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


def test_role_has_administrator_access_policy(iam_client, github_actions_role_name):
    """Verify role has AdministratorAccess policy attached."""
    response = iam_client.list_attached_role_policies(RoleName=github_actions_role_name)
    policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
    admin_policy = "arn:aws:iam::aws:policy/AdministratorAccess"
    assert admin_policy in policy_arns, (
        f"Role missing AdministratorAccess policy. Attached policies: {policy_arns}"
    )


@pytest.mark.skipif(not _is_github_actions(), reason="Only runs in GitHub Actions")
def test_current_identity_uses_expected_role(current_identity, github_actions_role_arn):
    """Verify current execution context is using the expected role."""
    current_arn = current_identity["Arn"]
    role_name = github_actions_role_arn.split("/")[-1]
    assert role_name in current_arn, (
        f"Current identity ({current_arn}) does not appear to be using "
        f"the expected role ({github_actions_role_arn})"
    )
