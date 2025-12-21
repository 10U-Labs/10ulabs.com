"""Layer 3: Wiring tests for api/shared/ecs_runner post-deployment.

Tests that components are connected. Assumes existence and configuration passed.

Three-layer testing model:
- Layer 3: Wiring - Components connected properly

For ECR, wiring tests verify that the authorization mechanism works, enabling
other components (ECS tasks, CI/CD) to authenticate and use the repository.
"""

import pytest


pytestmark = pytest.mark.layer(3)


class TestECRAuthorizationWiring:
    """Layer 3: Verify ECR authorization works for connecting services."""

    def test_runners_ecr_get_authorization_token_returns_auth_data_key(
        self, ecr_client
    ):
        """Verify get_authorization_token returns authorizationData key."""
        response = ecr_client.get_authorization_token()
        assert "authorizationData" in response, (
            "ECR get_authorization_token did not return authorizationData. "
            "Docker clients will not be able to authenticate."
        )

    def test_runners_ecr_get_authorization_token_returns_non_empty_auth_data(
        self, ecr_client
    ):
        """Verify get_authorization_token returns non-empty authorizationData."""
        response = ecr_client.get_authorization_token()
        assert len(response["authorizationData"]) > 0, (
            "ECR get_authorization_token returned empty authorizationData. "
            "Docker clients will not be able to authenticate."
        )

    def test_runners_ecr_authorization_data_has_token_key(self, ecr_client):
        """Verify authorization data contains authorizationToken key."""
        response = ecr_client.get_authorization_token()
        auth_data = response["authorizationData"][0]
        assert "authorizationToken" in auth_data, (
            "ECR authorizationData missing 'authorizationToken' field"
        )

    def test_runners_ecr_authorization_token_is_non_empty(self, ecr_client):
        """Verify authorization token is non-empty."""
        response = ecr_client.get_authorization_token()
        auth_data = response["authorizationData"][0]
        assert auth_data["authorizationToken"], (
            "ECR authorizationToken is empty"
        )

    def test_runners_ecr_authorization_data_has_proxy_endpoint_key(self, ecr_client):
        """Verify authorization data contains proxyEndpoint key."""
        response = ecr_client.get_authorization_token()
        auth_data = response["authorizationData"][0]
        assert "proxyEndpoint" in auth_data, (
            "ECR authorizationData missing 'proxyEndpoint' field. "
            "Docker clients need this to know which registry to authenticate to."
        )

    def test_runners_ecr_proxy_endpoint_uses_https(self, ecr_client):
        """Verify proxy endpoint uses HTTPS protocol."""
        response = ecr_client.get_authorization_token()
        auth_data = response["authorizationData"][0]
        assert auth_data["proxyEndpoint"].startswith("https://"), (
            f"ECR proxyEndpoint has unexpected format: {auth_data['proxyEndpoint']}"
        )
