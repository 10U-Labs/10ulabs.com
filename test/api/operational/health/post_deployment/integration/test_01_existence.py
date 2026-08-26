from test_fixtures.integration import create_lambda_existence_tests


TestDeployedResourcesExist = create_lambda_existence_tests(
    function_name_config_key="health_handler_function_name",
    default_function_name="TenULabsHealthHandler",
    terraform_path="src/api/operational/health/",
    log_group_fixture="health_handler_log_group",
)
