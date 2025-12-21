"""Layer 1: Authentication tests for bootstrap pre-deployment validation.

Verify AWS credentials are valid before testing authorization or state.
"""


def test_aws_credentials_valid(sts_client):
    """Verify AWS credentials are valid."""
    response = sts_client.get_caller_identity()
    assert response["Account"] is not None


def test_aws_credentials_not_expired(sts_client):
    """Verify AWS credentials are not expired."""
    response = sts_client.get_caller_identity()
    assert "Arn" in response
