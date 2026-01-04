"""Layer 1: Authentication - Verify AWS credentials are available and valid."""
import pytest
from botocore.exceptions import ClientError, NoCredentialsError



class TestAWSCredentialsExistence:
    """Layer 1: Verify AWS credentials are available and valid."""

    def test_credentials_available(self, sts_client):
        """Verify AWS credentials are configured."""
        assert sts_client is not None, (
            "No AWS credentials found. Configure via environment, "
            "~/.aws/credentials, or IAM role."
        )

    def test_can_call_sts_api(self, sts_client):
        """Verify credentials are valid by calling STS API."""
        try:
            response = sts_client.get_caller_identity()
            assert "Account" in response, "STS response missing Account field"
        except NoCredentialsError:
            pytest.fail(
                "No AWS credentials found. Configure via environment, "
                "~/.aws/credentials, or IAM role."
            )
        except ClientError as e:
            pytest.fail(f"Credentials invalid or expired: {e}")
