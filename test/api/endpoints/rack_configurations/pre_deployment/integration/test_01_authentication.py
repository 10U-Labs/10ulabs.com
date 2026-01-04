"""Layer 1: Authentication tests for rack_configurations endpoint pre-deployment.

Tests ONLY that AWS credentials are valid. No authorization or resource checks.

Six-layer testing model:
- Layer 1: Authentication - Valid credentials exist
"""

from test_fixtures.integration import Layer1EndpointAuthenticationTests




class TestAWSAuthentication(Layer1EndpointAuthenticationTests):
    """Layer 1: Verify AWS credentials are valid.

    All tests inherited from base class.
    """
