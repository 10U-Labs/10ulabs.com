"""Layer 2 tests: Verify permission to call API Gateway APIs.

These tests verify we have the necessary IAM permissions to inspect
the API Gateway integration that sends webhooks to the FIFO queue.
"""
import pytest
from botocore.exceptions import ClientError


class TestAPIGatewayAuthorization:
    """Layer 2: Verify permission to call API Gateway APIs."""

    def test_can_call_get_rest_apis(self, apigateway_client):
        """Verify we have permission to list REST APIs."""
        try:
            apigateway_client.get_rest_apis(limit=1)
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call apigateway:GetRestApis. "
                    "Check IAM policy has apigateway:GET permissions."
                )
            raise
