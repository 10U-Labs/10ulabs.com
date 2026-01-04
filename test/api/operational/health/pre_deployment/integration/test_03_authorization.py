"""Layer 3: Authorization tests for health endpoint pre-deployment.

Tests that credentials have permission to INSPECT prerequisite resources.
Not existence, not capability - just authorization to check.

Seven-layer testing model:
- Layer 3: Authorization - Permission to inspect resources
"""

import pytest
from test_fixtures.integration import (
    Layer3APIGatewayAuthorizationTests,
    Layer3LambdaAndIAMAuthorizationTests,
)




class TestAPIGatewayAuthorization(Layer3APIGatewayAuthorizationTests):
    """Layer 3: Verify permission to inspect API Gateway resources.

    All tests inherited from Layer3APIGatewayAuthorizationTests base class.
    """


class TestLambdaAndIAMAuthorization(Layer3LambdaAndIAMAuthorizationTests):
    """Layer 3: Verify permission to inspect Lambda and IAM resources.

    All tests inherited from Layer3LambdaAndIAMAuthorizationTests base class.
    """
