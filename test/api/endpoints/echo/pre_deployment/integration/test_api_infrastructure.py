"""Tests to validate API infrastructure exists for echo endpoint."""


def test_api_backend_terraform_outputs_readable(api_backend_outputs):
    """Verify api_backend terraform outputs are accessible."""
    assert api_backend_outputs.get("api_gateway_rest_api_id"), \
        "api_gateway_rest_api_id output not found in api_backend"


def test_api_gateway_exists(apigateway_client, api_backend_outputs):
    """Verify the API Gateway exists and matches the terraform output."""
    api_id = api_backend_outputs.get("api_gateway_rest_api_id")
    response = apigateway_client.get_rest_api(restApiId=api_id)
    assert response["id"] == api_id
