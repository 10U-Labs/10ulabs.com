"""Layer 1: Authentication tests for api/common/docker_repository pre-deployment.

Tests ONLY that AWS credentials are valid. No authorization or resource checks.

Six-layer testing model:
- Layer 1: Authentication - Valid credentials exist
"""

from test_fixtures.integration import Layer1AuthenticationTests




class TestAWSAuthentication(Layer1AuthenticationTests):
    """Layer 1: Verify AWS credentials are valid."""
