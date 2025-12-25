"""Layer 6: Capability tests for contact endpoint pre-deployment.

Tests that you can perform required operations. Assumes configuration passed.
These tests verify we have the capability to deploy the contact endpoint.

Six-layer testing model:
- Layer 6: Capability - Can perform required operations
"""

import pytest
from test_fixtures.integration import create_layer6_capability_tests


pytestmark = pytest.mark.layer(6)


TestDeploymentCapabilities = create_layer6_capability_tests(
    frozenset({'lambda', 'iam', 'ssm'})
)
