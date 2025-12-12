"""Tests to validate API infrastructure exists for contact endpoint."""


def test_api_backend_outputs_contains_gateway_id(api_backend_outputs):
    """Verify api_backend terraform outputs contain api_gateway_rest_api_id."""
    assert api_backend_outputs.get("api_gateway_rest_api_id")


def test_api_gateway_is_accessible(apigateway_client, api_backend_outputs):
    """Verify the API Gateway is accessible for contact endpoint."""
    api_id = api_backend_outputs.get("api_gateway_rest_api_id")
    response = apigateway_client.get_rest_api(restApiId=api_id)
    assert response["id"] == api_id
