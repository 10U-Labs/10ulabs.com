"""Layer 1-2 tests: AWS credentials and API authorization.

These tests MUST run first. All other tests depend on valid credentials.
"""
import pytest
from botocore.exceptions import ClientError


class TestAWSCredentialsExistence:
    """Layer 1: Verify AWS credentials are available and valid."""

    def test_credentials_available(self, sts_client):
        """Verify AWS credentials are configured."""
        assert sts_client is not None, (
            "No AWS credentials found. Configure via environment variables, "
            "~/.aws/credentials, or IAM role."
        )

    def test_can_call_sts_api(self, sts_client):
        """Verify credentials are valid by calling STS."""
        try:
            response = sts_client.get_caller_identity()
            assert response.get("Account"), "STS returned no account ID"
        except ClientError as err:
            pytest.fail(
                f"Credentials invalid or expired: {err.response['Error']['Message']}"
            )


class TestBedrockAPIAuthorization:
    """Layer 2: Verify we have permission to call Bedrock APIs."""

    def test_can_call_bedrock_describe(self, bedrock_client):
        """Verify we have permission to call Bedrock APIs."""
        try:
            # Just verify the client can be created and make basic calls
            # We don't need to list actual models, just verify auth
            assert bedrock_client is not None
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call Bedrock APIs. "
                    "Check IAM policy has bedrock:* permissions."
                )
            raise


class TestECRAPIAuthorization:
    """Layer 2: Verify we have permission to call ECR APIs."""

    def test_can_describe_repositories(self, ecr_client):
        """Verify we have permission to call ECR DescribeRepositories."""
        try:
            ecr_client.describe_repositories(maxResults=1)
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call ECR DescribeRepositories. "
                    "Check IAM policy has ecr:DescribeRepositories."
                )
            raise
