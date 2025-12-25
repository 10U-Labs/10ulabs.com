"""Layer 1: Authentication tests for www_shared pre-deployment validation.

Verify AWS credentials are valid before testing authorization, existence, or capability.
"""
import pytest
from test_fixtures.integration import create_simple_layer1_authentication_tests

pytestmark = pytest.mark.layer(1)

TestAWSAuthentication = create_simple_layer1_authentication_tests()
