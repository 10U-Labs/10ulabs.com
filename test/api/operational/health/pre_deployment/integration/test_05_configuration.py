"""Layer 5: Configuration tests for health endpoint pre-deployment.

Tests that prerequisite resources are configured correctly.
Assumes existence tests passed.

Six-layer testing model:
- Layer 5: Configuration - Prerequisites configured correctly
"""

import pytest


pytestmark = pytest.mark.layer(5)


class TestAPIGatewayConfiguration:
    """Layer 5: Verify API Gateway prerequisite is configured correctly."""

    def test_api_gateway_has_health_resource(self, api_gateway_info):
        """Verify API Gateway has /health resource path."""
        if api_gateway_info["id"] is None:
            pytest.skip("api_gateway_rest_api_id output not available")
        if not api_gateway_info["exists"]:
            pytest.skip("API Gateway does not exist")
        paths = api_gateway_info.get("paths", [])
        assert "/health" in paths, (
            f"API Gateway '{api_gateway_info['id']}' missing /health resource. "
            f"Available paths: {paths}"
        )

    def test_api_gateway_is_regional(self, api_gateway_info):
        """Verify API Gateway endpoint type is REGIONAL."""
        if api_gateway_info["id"] is None:
            pytest.skip("api_gateway_rest_api_id output not available")
        if not api_gateway_info["exists"]:
            pytest.skip("API Gateway does not exist")
        types = api_gateway_info.get("endpoint_types", [])
        assert "REGIONAL" in types, (
            f"API Gateway '{api_gateway_info['id']}' should be REGIONAL, got: {types}"
        )
