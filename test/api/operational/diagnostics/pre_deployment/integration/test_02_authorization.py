"""Layer 2: Authorization tests for diagnostics endpoint pre-deployment.

Tests that credentials have permission to INSPECT prerequisite resources.
Not existence, not capability - just authorization to check.

Six-layer testing model:
- Layer 2: Authorization - Permission to inspect resources
"""

import pytest
from test_fixtures.integration import (
    Layer2APIGatewayAuthorizationTests,
    Layer2LambdaAndIAMAuthorizationTests,
)


pytestmark = pytest.mark.layer(2)


class TestAPIGatewayAuthorization(Layer2APIGatewayAuthorizationTests):
    """Layer 2: Verify permission to inspect API Gateway resources."""

    pass  # All tests inherited from base class


class TestLambdaAndIAMAuthorization(Layer2LambdaAndIAMAuthorizationTests):
    """Layer 2: Verify permission to inspect Lambda and IAM resources."""

    pass  # All tests inherited from base class
