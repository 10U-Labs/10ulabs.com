"""Layer 5: Configuration tests for api_backend pre-deployment validation.

Verify prerequisite resources are configured correctly (assumes existence passed).
"""
import pytest
from botocore.exceptions import ClientError

pytestmark = pytest.mark.layer(5)


def test_iam_role_has_administrator_access(iam_client, current_role_name):
    """Verify the role has AdministratorAccess policy attached."""
    if not current_role_name:
        pytest.skip("Could not determine current role name")
    try:
        response = iam_client.list_attached_role_policies(RoleName=current_role_name)
        policy_names = [p["PolicyName"] for p in response["AttachedPolicies"]]
        assert "AdministratorAccess" in policy_names, (
            f"Role '{current_role_name}' missing AdministratorAccess policy. "
            f"Attached policies: {policy_names}"
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.skip("Cannot verify - no permission to list attached policies")
        raise
