"""Layer 6: Configuration tests for runners endpoint pre-deployment validation.

Verify prerequisite resources are configured correctly (assumes existence passed).
"""
import pytest
from botocore.exceptions import ClientError



class TestAPIGatewayAndStateBucketConfiguration:
    """Verify API Gateway and state bucket are configured correctly."""

    def test_api_gateway_is_regional(self, apigateway_client, api_gateway_id):
        """Verify API Gateway is configured as REGIONAL (not EDGE or PRIVATE)."""
        response = apigateway_client.get_rest_api(restApiId=api_gateway_id)
        endpoint_config = response.get("endpointConfiguration", {})
        endpoint_types = endpoint_config.get("types", [])
        assert "REGIONAL" in endpoint_types, (
            f"API Gateway {api_gateway_id} is not REGIONAL. "
            f"Configured types: {endpoint_types}. "
            "The runners endpoint requires a REGIONAL API Gateway."
        )

    def test_state_bucket_has_versioning(self, s3_client, state_bucket_name):
        """Verify state bucket has versioning enabled or was enabled (Suspended)."""
        try:
            response = s3_client.get_bucket_versioning(Bucket=state_bucket_name)
            status = response.get("Status", "")
            # Enabled = versioning active, Suspended = was enabled (versions preserved)
            assert status in ("Enabled", "Suspended"), (
                f"State bucket '{state_bucket_name}' has never had versioning enabled. "
                "Terraform state buckets should have versioning for safety."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] in ("AccessDenied", "AccessDeniedException"):
                pytest.skip("No permission to check bucket versioning")
            raise


class TestGitHubActionsRoleConfiguration:
    """Verify GitHub Actions role is configured correctly."""

    def test_github_actions_role_has_trust_policy(
        self, iam_client, github_actions_role_name
    ):
        """Verify GitHub Actions role has a trust policy."""
        response = iam_client.get_role(RoleName=github_actions_role_name)
        trust_policy = response["Role"].get("AssumeRolePolicyDocument", {})
        statements = trust_policy.get("Statement", [])
        assert len(statements) > 0, (
            f"GitHub Actions role '{github_actions_role_name}' has no trust policy. "
            "Check src/bootstrap/iam.tf for the trust relationship."
        )

    def test_github_actions_role_allows_sts_assume_role(
        self, iam_client, github_actions_role_name
    ):
        """Verify GitHub Actions role allows sts:AssumeRoleWithWebIdentity."""
        response = iam_client.get_role(RoleName=github_actions_role_name)
        trust_policy = response["Role"].get("AssumeRolePolicyDocument", {})
        statements = trust_policy.get("Statement", [])

        allowed_actions = []
        for stmt in statements:
            action = stmt.get("Action", [])
            if isinstance(action, str):
                allowed_actions.append(action)
            else:
                allowed_actions.extend(action)

        assert any("AssumeRole" in a for a in allowed_actions), (
            f"GitHub Actions role '{github_actions_role_name}' does not allow "
            "sts:AssumeRole or sts:AssumeRoleWithWebIdentity. "
            "Check src/bootstrap/iam.tf for the trust relationship."
        )
