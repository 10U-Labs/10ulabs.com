"""Layer 3 tests: Verify API Gateway resources exist.

These tests verify that the API Gateway REST API and /v1/agents
resource exist before checking their configuration.
"""
import pytest


class TestAPIGatewayResourcesExist:
    """Layer 3: Verify API Gateway resources exist."""

    def test_rest_api_exists(self, apigateway_client, api_gateway_id):
        """Verify the REST API exists."""
        if not api_gateway_id:
            pytest.skip("api_gateway_id not found in shared config")

        response = apigateway_client.get_rest_api(restApiId=api_gateway_id)
        assert response.get("id") == api_gateway_id, (
            f"REST API {api_gateway_id} not found"
        )

    def test_agents_resource_exists(self, apigateway_client, api_gateway_id):
        """Verify the /v1/agents resource exists."""
        if not api_gateway_id:
            pytest.skip("api_gateway_id not found in shared config")

        # Get all resources and find /v1/agents
        resources = apigateway_client.get_resources(restApiId=api_gateway_id)
        paths = [r.get("path") for r in resources.get("items", [])]

        assert "/v1/agents" in paths, (
            f"/v1/agents resource not found. Available paths: {paths}"
        )
