"""Layer 3: Authorization tests for soc_simulations endpoint.

Tests that credentials have permission to INSPECT prerequisite resources.
Not existence, not capability - just authorization to check.
"""
import pytest
from botocore.exceptions import ClientError

from test_fixtures.integration import (
    Layer3APIGatewayAuthorizationTests,
    Layer3LambdaAndIAMAuthorizationTests,
)

pytestmark = pytest.mark.layer(3)

pytest_plugins = ['test_fixtures.aws']


class TestAPIGatewayAuthorization(Layer3APIGatewayAuthorizationTests):
    """Authorization tests for API Gateway inspection."""


class TestLambdaAndIAMAuthorization(Layer3LambdaAndIAMAuthorizationTests):
    """Authorization tests for Lambda and IAM inspection."""


def test_can_list_kms_keys(kms_client):
    """Verify permission to list KMS keys."""
    try:
        kms_client.list_keys(Limit=1)
        can_list = True
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDeniedException":
            can_list = False
        else:
            raise
    assert can_list, "No permission to list KMS keys"
