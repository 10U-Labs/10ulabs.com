"""Layer 5: Configuration tests for health endpoint pre-deployment.

Tests that prerequisite resources are configured correctly.
Assumes existence tests passed.

Six-layer testing model:
- Layer 5: Configuration - Prerequisites configured correctly
"""

import pytest
from test_fixtures.integration import (
    Layer5APIGatewayRegionalTests,
    skip_if_api_gateway_unavailable,
)


pytestmark = pytest.mark.layer(5)


class TestAPIGatewayConfiguration(Layer5APIGatewayRegionalTests):
    """Layer 5: Verify API Gateway prerequisite is configured correctly."""

    def test_api_gateway_has_health_resource(self, api_gateway_info):
        """Verify API Gateway has /health resource path."""
        skip_if_api_gateway_unavailable(api_gateway_info)
        paths = api_gateway_info.get("paths", [])
        assert "/health" in paths, (
            f"API Gateway '{api_gateway_info['id']}' missing /health resource. "
            f"Available paths: {paths}"
        )
