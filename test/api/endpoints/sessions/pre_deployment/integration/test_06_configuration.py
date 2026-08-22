"""Layer 6: Configuration tests for sessions endpoint.

Configuration tests verify that prerequisite resources are configured correctly.
These are resources created by OTHER workflows that must be properly configured.
"""
import pytest


def test_api_gateway_configuration(apigateway_client, api_gateway_id):
    """Verify API Gateway has /v1 resource."""
    if api_gateway_id is None:
        pytest.skip("API Gateway ID not available")
    response = apigateway_client.get_resources(restApiId=api_gateway_id)
    paths = [r.get("path") for r in response.get("items", [])]
    assert "/v1" in paths or any(p.startswith("/v1") for p in paths)
