"""Layer 1: Authentication tests.

Verify AWS credentials are available and valid.
"""
import pytest
from test_fixtures.integration import create_layer1_authentication_tests


TestAWSAuthentication = create_layer1_authentication_tests()
