"""Tests to validate API infrastructure exists for rack_designer endpoint."""


def test_api_backend_outputs_provides_gateway_id(api_backend_outputs):
    """Verify api_backend terraform outputs provide api_gateway_rest_api_id."""
    assert api_backend_outputs.get("api_gateway_rest_api_id")


def test_api_gateway_reachable(apigateway_client, api_backend_outputs):
    """Verify the API Gateway is reachable for rack_designer endpoint."""
    api_id = api_backend_outputs.get("api_gateway_rest_api_id")
    response = apigateway_client.get_rest_api(restApiId=api_id)
    assert response["id"] == api_id
