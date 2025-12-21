"""Layer 1: Authentication tests.

Verify AWS credentials are available and valid.
"""
import pytest
from botocore.exceptions import ClientError

pytestmark = pytest.mark.layer(1)


def test_credentials_available(sts_client):
    """Verify AWS credentials are configured."""
    assert sts_client is not None, (
        "No AWS credentials found. Configure via environment variables, "
        "~/.aws/credentials, or IAM role."
    )


def test_can_call_sts_api(sts_client):
    """Verify credentials are valid by calling STS."""
    try:
        response = sts_client.get_caller_identity()
        assert response.get("Account"), "STS returned no account ID"
    except ClientError as e:
        pytest.fail(
            f"Credentials invalid or expired: {e.response['Error']['Message']}"
        )
