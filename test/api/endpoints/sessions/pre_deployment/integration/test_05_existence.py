import pytest


def test_api_gateway_existence(apigateway_client, api_gateway_id):
    if api_gateway_id is None:
        pytest.skip("API Gateway ID not available from terraform output")
    response = apigateway_client.get_rest_api(restApiId=api_gateway_id)
    assert response["id"] == api_gateway_id


def test_terraform_state_existence(s3_client, state_bucket_name):
    response = s3_client.head_bucket(Bucket=state_bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
