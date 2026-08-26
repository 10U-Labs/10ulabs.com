from test_fixtures.integration import (
    Layer5APIGatewayRegionalTests,
    skip_if_api_gateway_unavailable,
)


class TestAPIGatewayConfiguration(Layer5APIGatewayRegionalTests):
    def test_api_gateway_has_diagnostics_resource(self, api_gateway_info):
        skip_if_api_gateway_unavailable(api_gateway_info)
        paths = api_gateway_info.get("paths", [])
        assert "/diagnostics" in paths or "/diagnostics/echo" in paths, (
            f"API Gateway '{api_gateway_info['id']}' missing /diagnostics resource. "
            f"Available paths: {paths}"
        )
