"""Layer 5: Configuration tests for rack_configurations endpoint pre-deployment.

Tests that prerequisite resources are configured correctly.
Assumes existence passed. Not capability - just configuration.

Six-layer testing model:
- Layer 5: Configuration - Prerequisites configured correctly
"""

import pytest
from test_fixtures.integration import skip_if_api_gateway_unavailable


pytestmark = pytest.mark.layer(5)


class TestAPIGatewayConfiguration:
    """Layer 5: Verify API Gateway is configured correctly."""

    def test_api_gateway_is_regional(self, api_gateway_info):
        """Verify API Gateway is configured as regional endpoint."""
        skip_if_api_gateway_unavailable(api_gateway_info)
        endpoint_types = api_gateway_info.get("endpoint_types", [])
        assert "REGIONAL" in endpoint_types, (
            f"API Gateway '{api_gateway_info['id']}' is not regional. "
            f"Endpoint types: {endpoint_types}"
        )

    def test_api_gateway_has_v1_resource(self, api_gateway_info):
        """Verify API Gateway has /v1 resource for versioned API."""
        skip_if_api_gateway_unavailable(api_gateway_info)
        paths = api_gateway_info.get("paths", [])
        has_v1 = any(path.startswith("/v1") for path in paths)
        assert has_v1, (
            f"API Gateway '{api_gateway_info['id']}' missing /v1 resource. "
            f"Available paths: {paths}"
        )
