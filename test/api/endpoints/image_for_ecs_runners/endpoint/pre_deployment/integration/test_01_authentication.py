"""Layer 1: Authentication tests.

Verify AWS credentials are available and valid.
"""
import pytest
from test_fixtures.integration import create_layer1_authentication_tests

pytestmark = pytest.mark.layer(1)

TestAWSAuthentication = create_layer1_authentication_tests()
