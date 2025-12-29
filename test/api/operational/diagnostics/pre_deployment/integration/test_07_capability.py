"""Layer 7: Capability tests for diagnostics endpoint pre-deployment.

Tests that you can perform required operations. Assumes configuration passed.
Tests permissions needed for deployment (not runtime permissions).

Seven-layer testing model:
- Layer 7: Capability - Can perform required operations
"""

import pytest
from test_fixtures.integration import Layer6DeploymentCapabilityTests


pytestmark = pytest.mark.layer(7)


class TestDeploymentCapabilities(Layer6DeploymentCapabilityTests):
    """Layer 7: Verify capabilities to deploy Lambda, CloudWatch, and IAM.

    All tests inherited from Layer6DeploymentCapabilityTests.
    """
