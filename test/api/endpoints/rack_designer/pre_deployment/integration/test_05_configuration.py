"""Layer 5: Configuration tests for rack_designer endpoint pre-deployment.

Tests that prerequisite resources are configured correctly.
Assumes existence passed. Not capability - just configuration.

Six-layer testing model:
- Layer 5: Configuration - Prerequisites configured correctly
"""

import pytest


pytestmark = pytest.mark.layer(5)


class TestAPIGatewayConfiguration:
    """Layer 5: Verify API Gateway is configured correctly."""

    def test_api_gateway_is_regional(self, api_gateway_info):
        """Verify API Gateway is configured as regional endpoint."""
        if api_gateway_info["id"] is None:
            pytest.skip("api_gateway_rest_api_id output not available")
        if not api_gateway_info["exists"]:
            pytest.skip("API Gateway does not exist")
        endpoint_types = api_gateway_info.get("endpoint_types", [])
        assert "REGIONAL" in endpoint_types, (
            f"API Gateway '{api_gateway_info['id']}' is not regional. "
            f"Endpoint types: {endpoint_types}"
        )

    def test_api_gateway_has_v1_resource(self, api_gateway_info):
        """Verify API Gateway has /v1 resource for versioned API."""
        if api_gateway_info["id"] is None:
            pytest.skip("api_gateway_rest_api_id output not available")
        if not api_gateway_info["exists"]:
            pytest.skip("API Gateway does not exist")
        paths = api_gateway_info.get("paths", [])
        has_v1 = any(path.startswith("/v1") for path in paths)
        assert has_v1, (
            f"API Gateway '{api_gateway_info['id']}' missing /v1 resource. "
            f"Available paths: {paths}"
        )
