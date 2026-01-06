"""Layer 7: Capability tests for rack_configurations endpoint pre-deployment.

Tests that you can perform required operations. Assumes configuration passed.
These tests verify we have the capability to deploy the rack_configurations endpoint.

Seven-layer testing model:
- Layer 7: Capability - Can perform required operations
"""

from test_fixtures.integration import create_layer6_capability_tests




# Note: create_layer6_capability_tests factory is named for legacy compatibility
# but provides Layer 7 capability testing per the 7-layer model
TestDeploymentCapabilities = create_layer6_capability_tests(
    frozenset({'lambda', 'iam', 'dynamodb', 'logs'})
)
