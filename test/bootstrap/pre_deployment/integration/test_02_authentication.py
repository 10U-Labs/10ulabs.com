"""Layer 2: Authentication tests for bootstrap pre-deployment validation.

Verify AWS credentials are valid before testing authorization or state.
"""
import pytest
from test_fixtures.integration import create_simple_layer1_authentication_tests


TestAWSAuthentication = create_simple_layer1_authentication_tests()
