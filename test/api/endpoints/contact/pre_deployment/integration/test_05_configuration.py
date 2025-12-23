"""Layer 5: Configuration tests for contact endpoint pre-deployment.

Tests that prerequisite resources are configured correctly.
Assumes existence passed.

Six-layer testing model:
- Layer 5: Configuration - Prerequisites configured correctly
"""

import pytest


pytestmark = pytest.mark.layer(5)


class TestPrerequisiteConfiguration:
    """Layer 5: Verify prerequisite resources are configured correctly."""

    def test_api_gateway_has_v1_resource(self, api_gateway_info):
        """Verify API Gateway has /v1 resource path."""
        if api_gateway_info["id"] is None:
            pytest.skip("api_gateway_rest_api_id output not available")
        if not api_gateway_info["exists"]:
            pytest.skip("API Gateway does not exist")
        paths = api_gateway_info.get("paths", [])
        assert "/v1" in paths or any(p.startswith("/v1") for p in paths), (
            f"API Gateway missing /v1 resource. Available paths: {paths}"
        )

    def test_api_gateway_is_regional(self, api_gateway_info):
        """Verify API Gateway uses regional endpoint."""
        if api_gateway_info["id"] is None:
            pytest.skip("api_gateway_rest_api_id output not available")
        if not api_gateway_info["exists"]:
            pytest.skip("API Gateway does not exist")
        endpoint_types = api_gateway_info.get("endpoint_types", [])
        assert "REGIONAL" in endpoint_types, (
            f"API Gateway should be REGIONAL, got: {endpoint_types}"
        )
