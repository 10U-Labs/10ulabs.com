"""Layer 1: Authentication tests.

These tests verify that AWS credentials are valid before proceeding
with any resource checks. If these tests fail, all subsequent layers
will also fail.
"""


def test_aws_credentials_valid(sts_client):
    """Verify AWS credentials are valid by calling GetCallerIdentity."""
    response = sts_client.get_caller_identity()

    assert response.get("Account") is not None


def test_aws_credentials_return_account_id(sts_client):
    """Verify GetCallerIdentity returns a valid AWS account ID."""
    response = sts_client.get_caller_identity()
    account_id = response.get("Account", "")

    assert account_id.isdigit()
    assert len(account_id) == 12


def test_aws_credentials_return_arn(sts_client):
    """Verify GetCallerIdentity returns an ARN."""
    response = sts_client.get_caller_identity()

    assert "Arn" in response
    assert response["Arn"].startswith("arn:aws:")
