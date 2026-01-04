"""Layer 2: Authentication tests for health endpoint pre-deployment.

Tests ONLY that AWS credentials are valid. No authorization or resource checks.

Seven-layer testing model:
- Layer 2: Authentication - Valid credentials exist
"""

import pytest
from test_fixtures.integration import Layer2EndpointAuthenticationTests




class TestAWSAuthentication(Layer2EndpointAuthenticationTests):
    """Layer 2: Verify AWS credentials are valid.

    All tests inherited from Layer2EndpointAuthenticationTests base class.
    """
