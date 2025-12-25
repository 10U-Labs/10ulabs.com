"""Layer 1: Authentication tests for api/shared/runners pre-deployment.

Tests ONLY that AWS credentials are valid. No authorization or resource checks.

Six-layer testing model:
- Layer 1: Authentication - Valid credentials exist
"""

import pytest
from test_fixtures.integration import Layer1AuthenticationTests


pytestmark = pytest.mark.layer(1)


class TestAWSAuthentication(Layer1AuthenticationTests):
    """Layer 1: Verify AWS credentials are valid."""

    pass  # All tests inherited from base class
