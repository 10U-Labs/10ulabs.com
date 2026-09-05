from typing import Any

from test_fixtures.integration import (
    create_deployed_resource_existence_tests,
    create_lambda_configuration_tests,
    create_log_group_configuration_tests,
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

TestDiagnosticsHandlerResourcesExist = create_deployed_resource_existence_tests(
    function_name_config_key='diagnostics_handler_function_name',
    default_function_name='TenULabsDiagnosticsHandler',
    handler_display_name='DiagnosticsHandler',
)


def test_diagnostics_handler_logs_in_text_format(
    diagnostics_handler_configuration: Any
) -> None:
    log_format = diagnostics_handler_configuration["LoggingConfig"]["LogFormat"]
    assert log_format == "Text", (
        f"Lambda logging config should use the Text log format, got: {log_format}"
    )


def test_diagnostics_handler_describes_itself_as_the_diagnostics_endpoint(
    diagnostics_handler_configuration: Any
) -> None:
    description = diagnostics_handler_configuration.get("Description", "")
    assert description == "Diagnostics endpoint for API", (
        f"Lambda description should name the diagnostics endpoint, got: {description}"
    )
