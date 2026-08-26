from test_fixtures.integration import (
    create_lambda_api_gateway_wiring_tests,
    create_lambda_iam_wiring_tests,
)


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
