"""Layer 3: Authorization tests for diagnostics endpoint pre-deployment.

Tests that credentials have permission to INSPECT prerequisite resources.
Not existence, not capability - just authorization to check.

Seven-layer testing model:
- Layer 3: Authorization - Permission to inspect resources
"""

import pytest
from test_fixtures.integration import (
    Layer2APIGatewayAuthorizationTests,
    Layer2LambdaAndIAMAuthorizationTests,
)


pytestmark = pytest.mark.layer(3)


class TestAPIGatewayAuthorization(Layer2APIGatewayAuthorizationTests):
    """Layer 3: Verify permission to inspect API Gateway resources.

    All tests inherited from Layer2APIGatewayAuthorizationTests.
    """


class TestLambdaAndIAMAuthorization(Layer2LambdaAndIAMAuthorizationTests):
    """Layer 3: Verify permission to inspect Lambda and IAM resources.

    All tests inherited from Layer2LambdaAndIAMAuthorizationTests.
    """
