"""Layer 7: Capability tests for runners endpoint pre-deployment validation.

Verify we can perform required operations (assumes configuration passed).
These tests focus on specific deployment capabilities, not just API authorization.
"""
import pytest
from botocore.exceptions import ClientError
from test_fixtures.integration import (
    Layer6IAMCapabilityTests,
    Layer6S3CapabilityTests,
    check_state_file_readable,
)



class TestS3StateCapabilities(Layer6S3CapabilityTests):
    """Verify S3 capabilities for Terraform state.

    Inherits standard S3 capability tests from base class.
    """

    def test_can_read_runners_state_file(self, s3_client, state_bucket_name):
        """Verify we can read the runners state file specifically."""
        check_state_file_readable(
            s3_client, state_bucket_name, "api/endpoints/runners/terraform.tfstate"
        )


class TestIAMCapabilities(Layer6IAMCapabilityTests):
    """Verify IAM capabilities for resource management.

    Inherits standard IAM capability tests from base class.
    """


class TestAPIGatewayCapabilities:
    """Verify API Gateway capabilities for deployment."""

    def test_can_get_api_gateway_resources(self, apigateway_client, api_gateway_id):
        """Verify we can list API Gateway resources."""
        try:
            apigateway_client.get_resources(restApiId=api_gateway_id, limit=1)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("AccessDenied", "AccessDeniedException"):
                pytest.fail(
                    f"No permission to call apigateway:GetResources on '{api_gateway_id}'. "
                    "Check IAM permissions for the GitHub Actions role."
                )
            if error_code == "NotFoundException":
                pytest.skip("API Gateway does not exist yet")
            raise

    def test_can_get_api_gateway_stages(self, apigateway_client, api_gateway_id):
        """Verify we can list API Gateway stages for deployment."""
        try:
            apigateway_client.get_stages(restApiId=api_gateway_id)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("AccessDenied", "AccessDeniedException"):
                pytest.fail(
                    f"No permission to call apigateway:GetStages on '{api_gateway_id}'. "
                    "Check IAM permissions for the GitHub Actions role."
                )
            if error_code == "NotFoundException":
                pytest.skip("API Gateway does not exist yet")
            raise
