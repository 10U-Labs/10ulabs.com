"""Layer 7: Capability tests for runners endpoint pre-deployment validation.

Verify we can perform required operations (assumes configuration passed).
These tests focus on specific deployment capabilities, not just API authorization.
"""
import pytest
from botocore.exceptions import ClientError
from test_fixtures.integration import Layer6IAMCapabilityTests, Layer6S3CapabilityTests

pytestmark = pytest.mark.layer(7)


class TestS3StateCapabilities(Layer6S3CapabilityTests):
    """Verify S3 capabilities for Terraform state.

    Inherits standard S3 capability tests from base class.
    """

    def test_can_read_runners_state_file(self, s3_client, state_bucket_name):
        """Verify we can read the runners state file specifically."""
        state_key = "api/endpoints/runners/terraform.tfstate"
        try:
            s3_client.head_object(Bucket=state_bucket_name, Key=state_key)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "403":
                pytest.fail(
                    f"No permission to read '{state_key}' from '{state_bucket_name}'. "
                    "Check IAM permissions for s3:GetObject."
                )
            if error_code == "404":
                pytest.skip("State file does not exist yet (first deployment)")
            raise


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
