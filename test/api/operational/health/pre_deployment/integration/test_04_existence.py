"""Layer 4: Existence tests for health endpoint pre-deployment.

Tests that prerequisite resources exist. Assumes authorization passed.
These tests verify that resources from OTHER workflows that THIS workflow
depends on exist before deployment.

Six-layer testing model:
- Layer 4: Existence - Prerequisite resources exist
"""

import pytest
from botocore.exceptions import ClientError


pytestmark = pytest.mark.layer(4)


class TestAPIBackendPrerequisites:
    """Layer 4: Verify api_backend prerequisites exist."""

    def test_api_gateway_rest_api_id_output_exists(self, api_backend_outputs):
        """Verify api_gateway_rest_api_id output is available from api_backend."""
        assert api_backend_outputs.get("api_gateway_rest_api_id"), (
            "api_gateway_rest_api_id output not found in api_backend. "
            "Run terraform apply in src/api/backend/"
        )

    def test_api_gateway_exists_in_aws(self, apigateway_client, api_backend_outputs):
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
