from test_fixtures.integration import (
    create_lambda_configuration_tests,
    create_log_group_configuration_tests,
    create_naming_convention_tests,
)


TestLambdaConfiguration = create_lambda_configuration_tests(
    function_name_config_key="diagnostics_handler_function_name",
    default_function_name="TenULabsDiagnosticsHandler",
    expected_handler="handler.lambda_handler",
)

TestCloudWatchLogsConfiguration = create_log_group_configuration_tests(
    log_group_fixture="diagnostics_handler_log_group",
    expected_retention=7,
)

TestNamingConventions = create_naming_convention_tests(
    function_name_config_key="diagnostics_handler_function_name",
    default_function_name="TenULabsDiagnosticsHandler",
)
