from test_fixtures.integration import skip_if_api_gateway_unavailable


class TestAPIGatewayConfiguration:
    def test_api_gateway_is_regional(self, api_gateway_info):
        skip_if_api_gateway_unavailable(api_gateway_info)
        endpoint_types = api_gateway_info.get("endpoint_types", [])
        assert "REGIONAL" in endpoint_types, (
            f"API Gateway '{api_gateway_info['id']}' is not regional. "
            f"Endpoint types: {endpoint_types}"
        )

    def test_api_gateway_has_v1_resource(self, api_gateway_info):
        skip_if_api_gateway_unavailable(api_gateway_info)
        paths = api_gateway_info.get("paths", [])
        has_v1 = any(path.startswith("/v1") for path in paths)
        assert has_v1, (
            f"API Gateway '{api_gateway_info['id']}' missing /v1 resource. "
            f"Available paths: {paths}"
        )
