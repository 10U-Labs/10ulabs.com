from test_fixtures.integration import (
    Layer6APIGatewayRegionalTests,
    skip_if_api_gateway_unavailable,
)


class TestAPIGatewayConfiguration(Layer6APIGatewayRegionalTests):
    def test_api_gateway_has_health_resource(self, api_gateway_info):
        skip_if_api_gateway_unavailable(api_gateway_info)
        paths = api_gateway_info.get("paths", [])
        assert "/health" in paths, (
            f"API Gateway '{api_gateway_info['id']}' missing /health resource. "
            f"Available paths: {paths}"
        )
