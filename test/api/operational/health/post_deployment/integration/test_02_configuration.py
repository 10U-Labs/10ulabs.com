from test_fixtures.integration import (
    create_lambda_configuration_tests,
    create_log_group_configuration_tests,
    create_naming_convention_tests,
    get_aws_account_id_via_cli,
)


TestLambdaConfiguration = create_lambda_configuration_tests(
    function_name_config_key="health_handler_function_name",
    default_function_name="TenULabsHealthHandler",
    expected_handler="handler.lambda_handler",
)

TestCloudWatchLogsConfiguration = create_log_group_configuration_tests(
    log_group_fixture="health_handler_log_group",
    expected_retention=7,
)

TestNamingConventions = create_naming_convention_tests(
    function_name_config_key="health_handler_function_name",
    default_function_name="TenULabsHealthHandler",
)


def test_health_handler_has_10_second_timeout(lambda_client, config):
    function_name = config.get(
        'health_handler_function_name', 'TenULabsHealthHandler'
    )
    response = lambda_client.get_function(FunctionName=function_name)
    timeout = response["Configuration"]["Timeout"]
    assert timeout == 10, (
        f"Lambda timeout should be 10 seconds, got: {timeout}"
    )


def test_health_handler_arn_names_the_authenticated_account(lambda_client, config):
    function_name = config.get(
        'health_handler_function_name', 'TenULabsHealthHandler'
    )
    response = lambda_client.get_function(FunctionName=function_name)
    account_in_arn = response["Configuration"]["FunctionArn"].split(":")[4]
    assert account_in_arn == get_aws_account_id_via_cli(), (
        f"Deployed ARN names account {account_in_arn}, not the authenticated one"
    )
