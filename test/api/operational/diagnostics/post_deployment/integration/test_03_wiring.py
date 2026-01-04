"""Layer 3: Wiring tests for diagnostics endpoint post-deployment.

Tests that components are connected. Assumes existence and configuration passed.
These tests verify that resources are properly wired together.

Three-layer testing model:
- Layer 3: Wiring - Components connected properly
"""

from test_fixtures.integration import (
    create_lambda_api_gateway_wiring_tests,
    create_lambda_iam_wiring_tests,
)




# Create wiring test classes for diagnostics handler
TestLambdaWiring = create_lambda_api_gateway_wiring_tests(
    function_name_config_key='diagnostics_handler_function_name',
    default_function_name='TenULabsDiagnosticsHandler',
)

TestIAMPolicyWiring = create_lambda_iam_wiring_tests(
    function_name_config_key='diagnostics_handler_function_name',
    default_function_name='TenULabsDiagnosticsHandler',
    check_basic_execution=True,
    check_lambda_trust=True,
)
