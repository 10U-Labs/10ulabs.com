"""Layer 2: Authentication tests for sessions endpoint.

Authentication tests verify that AWS credentials are valid.
No authorization or resource checks are performed.
"""
import pytest



class TestAwsAuthentication:
    """Tests for AWS authentication."""

    def test_aws_credentials_valid(self, sts_client):
        """Verify AWS credentials are valid."""
        response = sts_client.get_caller_identity()
        assert response["Account"] is not None

    def test_aws_credentials_not_expired(self, sts_client):
        """Verify AWS credentials are not expired."""
        response = sts_client.get_caller_identity()
        assert "Arn" in response
