"""Layer 6: Capability tests for ECS runner image deployment.

These tests verify that we can perform required operations.
Per PRE_DEPLOYMENT_INTEGRATION_TESTS.md tenets, capability tests
verify we can perform operations - assumes configuration tests passed.
"""
from botocore.exceptions import ClientError

import pytest

from test_fixtures.integration import handle_ecr_error



class TestECRCapability:
    """Verify we can perform required ECR operations."""

    def test_can_get_ecr_authorization_data(self, ecr_client):
        """Verify we can get ECR authorization data for docker push."""
        try:
            response = ecr_client.get_authorization_token()
            assert response.get("authorizationData"), (
                "ECR returned empty authorization data. "
                "Cannot authenticate to push Docker images."
            )
        except ClientError as e:
            pytest.fail(
                f"Failed to get ECR authorization token: {e.response['Error']['Message']}. "
                "This is required to push Docker images to ECR."
            )

    def test_ecr_authorization_token_not_empty(self, ecr_client):
        """Verify ECR authorization token is not empty."""
        try:
            response = ecr_client.get_authorization_token()
            if not response.get("authorizationData"):
                pytest.skip("No authorization data available")
            auth_data = response["authorizationData"][0]
            assert auth_data.get("authorizationToken"), (
                "ECR authorization token is empty. "
                "Cannot authenticate to push Docker images."
            )
        except ClientError as e:
            pytest.fail(
                f"Failed to get ECR authorization token: {e.response['Error']['Message']}. "
                "This is required to push Docker images to ECR."
            )

    def test_can_list_images_in_repository(self, ecr_client, api_common_ecr_outputs):
        """Verify we can list images in the ECR repository."""
        repository_name = api_common_ecr_outputs.get("repository_name")
        if not repository_name:
            pytest.skip("repository_name output not available")
        try:
            ecr_client.list_images(
                repositoryName=repository_name,
                maxResults=1
            )
        except ClientError as e:
            handle_ecr_error(e, "ecr:ListImages", repository_name)
        assert True  # Explicit pass
