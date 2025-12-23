"""Tests to validate API infrastructure exists for echo endpoint.

Five-layer testing model:
- Layer 3: Existence - Does the API Gateway exist?

These tests verify that api_backend resources this endpoint depends on exist.
"""

from botocore.exceptions import ClientError
import pytest


class TestAPIBackendInfrastructure:
    """Layer 3: Verify api_backend terraform outputs and API Gateway exist."""

    def test_api_gateway_rest_api_id_output_exists(self, api_backend_outputs):
        """Verify api_gateway_rest_api_id output is available."""
        assert api_backend_outputs.get("api_gateway_rest_api_id"), (
            "api_gateway_rest_api_id output not found in api_backend. "
            "Run terraform apply in src/api/backend/"
        )

    def test_api_gateway_exists(self, apigateway_client, api_backend_outputs):
        """Verify the API Gateway exists in AWS."""
        api_id = api_backend_outputs.get("api_gateway_rest_api_id")
        if not api_id:
            pytest.skip("api_gateway_rest_api_id output not available")
        try:
            response = apigateway_client.get_rest_api(restApiId=api_id)
            assert response["id"] == api_id, (
                f"API Gateway ID mismatch: expected {api_id}, got {response['id']}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NotFoundException":
                pytest.fail(
                    f"API Gateway '{api_id}' does not exist. "
                    "Run terraform apply in src/api/backend/"
                )
            raise
