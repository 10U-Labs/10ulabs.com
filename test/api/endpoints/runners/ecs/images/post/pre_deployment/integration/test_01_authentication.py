"""Layer 1: Authentication tests for ECS runner image deployment.

These tests verify that AWS credentials are valid.
Per PRE_DEPLOYMENT_INTEGRATION_TESTS.md tenets, authentication tests
only verify credentials are valid - no authorization or resource checks.
"""
from botocore.exceptions import NoCredentialsError, ClientError

import pytest

pytestmark = pytest.mark.layer(1)


class TestAWSCredentials:
    """Verify AWS credentials are valid."""

    def test_aws_credentials_valid(self, sts_client):
        """Verify AWS credentials are valid."""
        try:
            response = sts_client.get_caller_identity()
            assert response["Account"] is not None
        except NoCredentialsError:
            pytest.fail(
                "No AWS credentials found. "
                "Configure credentials via environment variables, "
                "~/.aws/credentials, or IAM role."
            )
        except ClientError as e:
            pytest.fail(
                f"Failed to call sts:GetCallerIdentity: {e.response['Error']['Message']}. "
                "Check AWS credentials are valid and not expired."
            )

    def test_aws_credentials_not_expired(self, sts_client):
        """Verify AWS credentials are not expired."""
        try:
            response = sts_client.get_caller_identity()
            assert "Arn" in response
        except ClientError as e:
            pytest.fail(
                f"AWS credentials may be expired: {e.response['Error']['Message']}"
            )
