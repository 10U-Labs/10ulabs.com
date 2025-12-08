"""Tests to validate api_backend infrastructure exists before endpoint_health deployment."""


def test_api_gateway_exists(apigateway_client, api_backend_outputs):
    """Verify the API Gateway exists."""
    api_id = api_backend_outputs.get("api_gateway_id")
    assert api_id, "api_gateway_id output not found in api_backend"
    response = apigateway_client.get_rest_api(restApiId=api_id)
    assert response["id"] == api_id


def test_lambda_execution_role_exists(iam_client, api_backend_outputs):
    """Verify the Lambda execution role exists."""
    role_arn = api_backend_outputs.get("lambda_execution_role_arn")
    assert role_arn, "lambda_execution_role_arn output not found in api_backend"
    role_name = role_arn.split("/")[-1]
    response = iam_client.get_role(RoleName=role_name)
    assert response["Role"]["RoleName"] == role_name
