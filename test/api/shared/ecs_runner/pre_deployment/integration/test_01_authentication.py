"""Layer 1: Authentication tests for api/shared/ecs_runner pre-deployment.

Tests ONLY that AWS credentials are valid. No authorization or resource checks.

Six-layer testing model:
- Layer 1: Authentication - Valid credentials exist
"""

from botocore.exceptions import ClientError, NoCredentialsError
import pytest


pytestmark = pytest.mark.layer(1)


class TestAWSAuthentication:
    """Layer 1: Verify AWS credentials are valid."""

    def test_aws_credentials_are_available(self, sts_client):
        """Verify AWS credentials are configured."""
        try:
            sts_client.get_caller_identity()
        except NoCredentialsError:
            pytest.fail(
                "No AWS credentials found. "
                "Configure credentials via environment variables, "
                "~/.aws/credentials, or IAM role."
            )

    def test_aws_credentials_are_valid(self, sts_client):
        """Verify we can call sts:GetCallerIdentity."""
        try:
            sts_client.get_caller_identity()
        except ClientError as e:
            pytest.fail(
                f"Failed to call sts:GetCallerIdentity: "
                f"{e.response['Error']['Message']}. "
                "Check AWS credentials are valid and not expired."
            )

    def test_aws_credentials_return_account(self, caller_identity):
        """Verify STS response contains Account."""
        assert "Account" in caller_identity, (
            "STS GetCallerIdentity response missing 'Account' field. "
            "AWS credentials may be malformed."
        )

    def test_aws_credentials_return_arn(self, caller_identity):
        """Verify STS response contains Arn."""
        assert "Arn" in caller_identity, (
            "STS GetCallerIdentity response missing 'Arn' field. "
            "AWS credentials may be malformed."
        )

    def test_caller_identity_is_role(self, caller_identity):
        """Verify we are running as an IAM role (not user)."""
        arn = caller_identity.get("Arn", "")
        assert ":assumed-role/" in arn or ":role/" in arn, (
            f"Expected to be running as IAM role, but running as: {arn}. "
            "GitHub Actions should assume the GitHub Actions OIDC role."
        )
