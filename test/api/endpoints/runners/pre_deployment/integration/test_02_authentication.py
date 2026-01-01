"""Layer 2: Authentication tests for runners endpoint pre-deployment validation.

Verify AWS credentials are valid before testing authorization or state.
"""
import pytest
from botocore.exceptions import NoCredentialsError

pytestmark = pytest.mark.layer(2)


def test_aws_credentials_available(sts_client):
    """Verify AWS credentials are configured."""
    try:
        sts_client.get_caller_identity()
    except NoCredentialsError:
        pytest.fail(
            "No AWS credentials found. "
            "Configure credentials via environment variables, "
            "~/.aws/credentials, or IAM role."
        )


def test_aws_credentials_valid(sts_client):
    """Verify AWS credentials are valid."""
    response = sts_client.get_caller_identity()
    assert response["Account"] is not None


def test_aws_credentials_not_expired(sts_client):
    """Verify AWS credentials are not expired."""
    response = sts_client.get_caller_identity()
    assert "Arn" in response


def test_caller_identity_is_role(current_identity):
    """Verify we are running as an IAM role (not user)."""
    arn = current_identity.get("Arn", "")
    assert ":assumed-role/" in arn or ":role/" in arn, (
        f"Expected to be running as IAM role, but running as: {arn}. "
        "GitHub Actions should assume the GitHub Actions OIDC role."
    )
