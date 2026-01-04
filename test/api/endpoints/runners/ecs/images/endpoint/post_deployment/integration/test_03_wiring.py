"""Layer 3: Wiring tests.

Verify components are connected properly.
"""
import pytest
from test_fixtures.integration import create_lambda_execution_role_wiring_tests



# Create Lambda execution role wiring tests using lambda_config fixture
TestLambdaExecutionRole = create_lambda_execution_role_wiring_tests(
    fixture_name="lambda_config"
)
