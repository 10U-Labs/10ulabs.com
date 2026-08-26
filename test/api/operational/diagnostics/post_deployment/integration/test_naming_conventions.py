from test_fixtures.integration import create_deployed_naming_convention_tests


_naming_tests = create_deployed_naming_convention_tests(
    function_name_config_key='diagnostics_handler_function_name',
    default_function_name='TenULabsDiagnosticsHandler',
    handler_display_name='DiagnosticsHandler',
)
TestDiagnosticsHandlerIAMRoleNamingConventions = _naming_tests[0]
TestDiagnosticsHandlerLambdaFunctionNamingConventions = _naming_tests[1]
