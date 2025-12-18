"""Layer 1: Authentication - Are AWS credentials configured and valid?

These tests MUST run first because all other tests depend on having valid AWS
credentials. If authentication fails, skip all subsequent layers.

Five-layer testing model:
- Layer 1: Authentication - Are credentials configured and valid? (THIS FILE)
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: Existence - Do the required resources exist?
- Layer 4: Configuration - Are resources configured correctly?
- Layer 5: Capability - Can we perform required operations?
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
