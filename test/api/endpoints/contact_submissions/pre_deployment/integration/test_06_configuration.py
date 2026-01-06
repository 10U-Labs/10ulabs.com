"""Layer 6: Configuration tests for contact endpoint pre-deployment.

Tests that prerequisite resources are configured correctly.
Assumes existence passed.

Seven-layer testing model:
- Layer 6: Configuration - Prerequisites configured correctly
"""
from test_fixtures.integration import skip_if_api_gateway_unavailable



class TestPrerequisiteConfiguration:
    """Layer 6: Verify prerequisite resources are configured correctly."""

    def test_api_gateway_has_v1_resource(self, api_gateway_info):
        """Verify API Gateway has /v1 resource path."""
        skip_if_api_gateway_unavailable(api_gateway_info)
        paths = api_gateway_info.get("paths", [])
        assert "/v1" in paths or any(p.startswith("/v1") for p in paths), (
            f"API Gateway missing /v1 resource. Available paths: {paths}"
        )

    def test_api_gateway_is_regional(self, api_gateway_info):
        """Verify API Gateway uses regional endpoint."""
        skip_if_api_gateway_unavailable(api_gateway_info)
        endpoint_types = api_gateway_info.get("endpoint_types", [])
        assert "REGIONAL" in endpoint_types, (
            f"API Gateway should be REGIONAL, got: {endpoint_types}"
        )
