"""Layer 3: Authorization tests for contact endpoint pre-deployment.

Tests that credentials have permission to INSPECT prerequisite resources.
Not existence, not capability - just authorization to check.

Seven-layer testing model:
- Layer 3: Authorization - Permission to inspect resources
"""
import pytest
from botocore.exceptions import ClientError
from test_fixtures.integration import (
    Layer3APIGatewayAuthorizationTests,
    Layer3LambdaAndIAMAuthorizationTests,
)



class TestAPIGatewayAuthorization(Layer3APIGatewayAuthorizationTests):
    """Layer 3: Verify permission to inspect API Gateway resources.

    All tests inherited from base class.
    """


class TestLambdaAndIAMAuthorization(Layer3LambdaAndIAMAuthorizationTests):
    """Layer 3: Verify permission to inspect Lambda and IAM resources.

    All tests inherited from base class.
    """


class TestSESAndSSMAuthorization:
    """Layer 2: Verify permission to inspect SES and SSM resources."""

    def test_can_get_account_sending_enabled(self, ses_client):
        """Verify permission to check SES account sending status."""
        try:
            ses_client.get_account_sending_enabled()
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail("No permission to check SES account sending status")
            raise
        assert True  # Explicit pass

    def test_can_list_identities(self, ses_client):
        """Verify permission to list SES identities."""
        try:
            ses_client.list_identities(MaxItems=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail("No permission to list SES identities")
            raise
        assert True  # Explicit pass

    def test_can_describe_parameters(self, ssm_client):
        """Verify permission to describe SSM parameters."""
        try:
            ssm_client.describe_parameters(MaxResults=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail("No permission to describe SSM parameters")
            raise
        assert True  # Explicit pass
