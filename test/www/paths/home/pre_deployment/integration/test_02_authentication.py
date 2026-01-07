"""Layer 2: Authentication tests for www home page deployment.

Test ONLY that credentials are valid. No authorization or resource checks.
"""
from test_fixtures.integration import Layer2EndpointAuthenticationTests


class TestAWSAuthentication(Layer2EndpointAuthenticationTests):
    """Layer 2: Verify AWS credentials are valid for deployment."""


class TestAWSCredentialsValid:
    """Layer 2: Additional authentication tests."""

    def test_aws_credentials_not_expired(self, sts_client):
        """Verify AWS credentials are not expired."""
        response = sts_client.get_caller_identity()
        has_arn = "Arn" in response
        assert has_arn, "AWS credentials may be expired"

    def test_aws_region_configured(self, aws_region):
        """Verify AWS region is configured."""
        region_is_configured = aws_region is not None and len(aws_region) > 0
        assert region_is_configured, "AWS region not configured"
