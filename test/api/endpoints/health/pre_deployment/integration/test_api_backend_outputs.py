"""Tests to validate api_backend infrastructure exists before endpoint_health deployment."""


def test_api_gateway_exists(apigateway_client, api_backend_outputs):
    """Verify the API Gateway exists."""
    api_id = api_backend_outputs.get("api_gateway_rest_api_id")
    assert api_id, "api_gateway_rest_api_id output not found in api_backend"
    response = apigateway_client.get_rest_api(restApiId=api_id)
    assert response["id"] == api_id
