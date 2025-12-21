"""Layer 2: Authorization tests for health endpoint pre-deployment.

Tests that credentials have permission to INSPECT prerequisite resources.
Not existence, not capability - just authorization to check.

Six-layer testing model:
- Layer 2: Authorization - Permission to inspect resources
"""

import pytest
from botocore.exceptions import ClientError


pytestmark = pytest.mark.layer(2)


class TestAPIGatewayAuthorization:
    """Layer 2: Verify permission to inspect API Gateway resources."""

    def test_can_describe_rest_apis(self, apigateway_client):
        """Verify permission to describe REST APIs."""
        try:
            apigateway_client.get_rest_apis(limit=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail("No permission to describe API Gateway REST APIs")
            raise

    def test_can_access_specific_rest_api(self, api_gateway_info):
        """Verify permission to describe specific REST API."""
        if api_gateway_info["id"] is None:
            pytest.skip("api_gateway_rest_api_id output not available")
        assert api_gateway_info["accessible"], (
            f"No permission to describe API Gateway '{api_gateway_info['id']}'"
        )


class TestLambdaAndIAMAuthorization:
    """Layer 2: Verify permission to inspect Lambda and IAM resources."""

    def test_can_list_functions(self, lambda_client):
        """Verify permission to list Lambda functions."""
        try:
            lambda_client.list_functions(MaxItems=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail("No permission to list Lambda functions")
            raise

    def test_can_list_roles(self, iam_client):
        """Verify permission to list IAM roles."""
        try:
            iam_client.list_roles(MaxItems=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail("No permission to list IAM roles")
            raise
