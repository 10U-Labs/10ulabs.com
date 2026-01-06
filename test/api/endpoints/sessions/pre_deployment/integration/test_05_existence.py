"""Layer 5: Existence tests for sessions endpoint.

Existence tests verify that prerequisite resources exist.
These are resources created by OTHER workflows that must exist before deployment.
"""


class TestApiGatewayExistence:
    """Tests for API Gateway prerequisite existence."""

    def test_api_gateway_exists(self, apigateway_client, api_gateway_id):
        """Verify API Gateway from api_common_routing exists."""
        if api_gateway_id is None:
            pytest.skip("API Gateway ID not available from terraform output")
        response = apigateway_client.get_rest_api(restApiId=api_gateway_id)
        assert response["id"] == api_gateway_id


class TestTerraformStateExistence:
    """Tests for Terraform state bucket existence."""

    def test_terraform_state_bucket_exists(self, s3_client, state_bucket_name):
        """Verify Terraform state bucket exists."""
        response = s3_client.head_bucket(Bucket=state_bucket_name)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
