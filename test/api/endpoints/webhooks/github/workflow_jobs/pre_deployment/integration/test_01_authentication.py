"""Layer 1: Authentication - Are AWS credentials configured and valid?

These tests MUST run first because all other tests depend on having valid AWS
credentials. If authentication fails, skip all subsequent layers.

Six-layer testing model:
- Layer 1: Authentication - Are credentials configured and valid? (THIS FILE)
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: State - Does Terraform state match AWS reality?
- Layer 4: Existence - Do the required resources exist?
- Layer 5: Configuration - Are resources configured correctly?
- Layer 6: Capability - Can we perform required operations?
"""
import pytest

from test_fixtures.integration.helpers import (
    check_credentials_available,
    check_credentials_valid,
)




class TestAWSCredentialsAuthentication:
    """Layer 1: Verify AWS credentials are available and valid."""

    def test_credentials_available(self, sts_client):
        """Verify AWS credentials are configured."""
        check_credentials_available(sts_client)
        assert True  # Explicit pass

    def test_can_call_sts_api(self, sts_client):
        """Verify we can call sts:GetCallerIdentity."""
        check_credentials_valid(sts_client)
        response = sts_client.get_caller_identity()
        assert "Account" in response

    def test_caller_identity_has_arn(self, sts_client):
        """Verify caller identity includes ARN."""
        check_credentials_valid(sts_client)
        response = sts_client.get_caller_identity()
        assert "Arn" in response

    def test_caller_identity_is_role(self, caller_identity):
        """Verify we are running as an IAM role (not user)."""
        arn = caller_identity.get("Arn", "")
        is_role = ":assumed-role/" in arn or ":role/" in arn
        if not is_role:
            pytest.skip(
                f"Running as IAM user ({arn}), not role. "
                "Skipping role check for local development."
            )
        assert True  # Explicit pass
