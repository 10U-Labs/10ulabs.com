"""Layer 6: Capability tests for diagnostics endpoint pre-deployment.

Tests that you can perform required operations. Assumes configuration passed.
Tests permissions needed for deployment (not runtime permissions).

Six-layer testing model:
- Layer 6: Capability - Can perform required operations
"""

import pytest
from test_fixtures.integration import Layer6DeploymentCapabilityTests


pytestmark = pytest.mark.layer(6)


class TestDeploymentCapabilities(Layer6DeploymentCapabilityTests):
    """Layer 6: Verify capabilities to deploy Lambda, CloudWatch, and IAM.

    All tests inherited from Layer6DeploymentCapabilityTests.
    """
