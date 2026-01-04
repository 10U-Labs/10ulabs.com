"""Layer 2: Authentication tests for diagnostics endpoint pre-deployment.

Tests ONLY that AWS credentials are valid. No authorization or resource checks.

Seven-layer testing model:
- Layer 2: Authentication - Valid credentials exist
"""

from test_fixtures.integration import Layer1EndpointAuthenticationTests




class TestAWSAuthentication(Layer1EndpointAuthenticationTests):
    """Layer 2: Verify AWS credentials are valid.

    All tests inherited from Layer1EndpointAuthenticationTests.
    """
