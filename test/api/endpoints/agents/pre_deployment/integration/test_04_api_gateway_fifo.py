"""Layer 4 tests: Verify API Gateway FIFO configuration.

These tests verify that the API Gateway integration is correctly
configured to send messages to a FIFO queue with MessageGroupId.
"""
import pytest


class TestAPIGatewayFIFOConfiguration:
    """Layer 4: Verify API Gateway FIFO integration configuration."""

    @pytest.fixture
    def agents_resource_id(self, apigateway_client, api_gateway_id):
        """Get the resource ID for /v1/agents."""
        if not api_gateway_id:
            pytest.skip("api_gateway_id not found in shared config")

        resources = apigateway_client.get_resources(restApiId=api_gateway_id)
        for resource in resources.get("items", []):
            if resource.get("path") == "/v1/agents":
                return resource.get("id")

        pytest.skip("/v1/agents resource not found")

    def test_integration_targets_fifo_queue(
        self, apigateway_client, api_gateway_id, agents_resource_id
    ):
        """Verify the integration URI targets a FIFO queue."""
        integration = apigateway_client.get_integration(
            restApiId=api_gateway_id,
            resourceId=agents_resource_id,
            httpMethod="POST"
        )

        uri = integration.get("uri", "")
        assert ".fifo" in uri, (
            f"Integration URI does not target FIFO queue. URI: {uri}"
        )

    def test_integration_sends_message_group_id(
        self, apigateway_client, api_gateway_id, agents_resource_id
    ):
        """Verify the request template includes MessageGroupId."""
        integration = apigateway_client.get_integration(
            restApiId=api_gateway_id,
            resourceId=agents_resource_id,
            httpMethod="POST"
        )

        templates = integration.get("requestTemplates", {})
        json_template = templates.get("application/json", "")

        assert "MessageGroupId" in json_template, (
            f"Request template missing MessageGroupId. Template: {json_template}"
        )
