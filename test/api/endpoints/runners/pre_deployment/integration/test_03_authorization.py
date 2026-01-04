"""Layer 3: Authorization tests for runners endpoint pre-deployment validation.

Verify permission to inspect prerequisite resources (not existence, not capability).
"""
import pytest
from botocore.exceptions import ClientError
from test_fixtures.integration import (
    Layer2S3AuthorizationTests,
    Layer3LambdaAndIAMAuthorizationTests,
)



class TestS3Authorization(Layer2S3AuthorizationTests):
    """Verify S3 authorization for state bucket.

    Inherits standard S3 authorization tests from base class.
    """


class TestLambdaAndIAMAuthorization(Layer3LambdaAndIAMAuthorizationTests):
    """Verify Lambda and IAM authorization for inspection.

    Inherits standard Lambda and IAM authorization tests from base class.
    """


class TestGitHubActionsAndAPIGatewayAuthorization:
    """Verify authorization for GitHub Actions role and API Gateway inspection."""

    def test_can_call_iam_get_role_on_gha_role(self, iam_client, github_actions_role_name):
        """Verify permission to call iam:GetRole on GitHub Actions role."""
        try:
            iam_client.get_role(RoleName=github_actions_role_name)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("AccessDenied", "AccessDeniedException"):
                pytest.fail(
                    f"No permission to call iam:GetRole on '{github_actions_role_name}'"
                )
            if error_code != "NoSuchEntity":
                raise

    def test_can_call_apigateway_get_rest_api(self, apigateway_client, api_gateway_id):
        """Verify permission to call apigateway:GetRestApi."""
        try:
            apigateway_client.get_rest_api(restApiId=api_gateway_id)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("AccessDeniedException", "AccessDenied"):
                pytest.fail(
                    f"No permission to call apigateway:GetRestApi on '{api_gateway_id}'"
                )
            if error_code != "NotFoundException":
                raise
