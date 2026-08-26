from test_fixtures.integration import create_lambda_existence_tests


TestDeployedResourcesExist = create_lambda_existence_tests(
    function_name_config_key="diagnostics_handler_function_name",
    default_function_name="TenULabsDiagnosticsHandler",
    terraform_path="src/api/operational/diagnostics/",
    log_group_fixture="diagnostics_handler_log_group",
)
