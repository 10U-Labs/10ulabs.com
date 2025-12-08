"""Tests to validate IAM permissions for ECR operations exist."""


def test_ecr_get_authorization_token_succeeds(ecr_client):
    """Verify current credentials have permission to get ECR authorization token.

    This permission is required for docker login to ECR before push/pull operations.
    """
    response = ecr_client.get_authorization_token()
    assert "authorizationData" in response
    assert len(response["authorizationData"]) > 0
    auth_data = response["authorizationData"][0]
    assert "authorizationToken" in auth_data
    assert auth_data["authorizationToken"]
