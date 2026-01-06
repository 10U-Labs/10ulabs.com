"""Layer 7: Capability tests for contact endpoint pre-deployment.

Tests that you can perform required operations. Assumes configuration passed.
These tests verify we have the capability to deploy the contact endpoint.

Seven-layer testing model:
- Layer 7: Capability - Can perform required operations
"""
from test_fixtures.integration import create_layer6_capability_tests



TestDeploymentCapabilities = create_layer6_capability_tests(
    frozenset({'lambda', 'iam', 'ssm'})
)
