"""Layer 1: Authentication tests for health endpoint pre-deployment.

Tests ONLY that AWS credentials are valid. No authorization or resource checks.

Six-layer testing model:
- Layer 1: Authentication - Valid credentials exist
"""

import pytest


pytestmark = pytest.mark.layer(1)


class TestAWSAuthentication:
    """Layer 1: Verify AWS credentials are valid."""

    def test_aws_credentials_are_valid(self, sts_client):
        """Verify AWS credentials are valid by calling GetCallerIdentity."""
        response = sts_client.get_caller_identity()
        assert response["Account"] is not None, (
            "AWS credentials invalid - GetCallerIdentity returned no Account"
        )

    def test_aws_credentials_return_account_id(self, sts_client):
        """Verify AWS credentials return a valid account ID."""
        response = sts_client.get_caller_identity()
        assert len(response["Account"]) == 12, (
            f"AWS account ID has unexpected length: {len(response['Account'])}"
        )

    def test_aws_credentials_return_arn(self, sts_client):
        """Verify AWS credentials return an ARN."""
        response = sts_client.get_caller_identity()
        assert "Arn" in response, "AWS credentials did not return an ARN"

    def test_aws_credentials_arn_has_valid_format(self, sts_client):
        """Verify AWS credentials ARN has valid format."""
        response = sts_client.get_caller_identity()
        assert response["Arn"].startswith("arn:aws:"), (
            f"ARN has unexpected format: {response['Arn']}"
        )
