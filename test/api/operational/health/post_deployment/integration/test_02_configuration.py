from typing import Any, Dict

from test_fixtures.integration import (
    create_lambda_configuration_tests,
    create_log_group_configuration_tests,
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

def test_health_handler_has_10_second_timeout(lambda_client: Any, config: Dict[str, Any]) -> None:
    function_name = config.get(
        'health_handler_function_name', 'TenULabsHealthHandler'
    )
    response = lambda_client.get_function(FunctionName=function_name)
    timeout = response["Configuration"]["Timeout"]
    assert timeout == 10, (
        f"Lambda timeout should be 10 seconds, got: {timeout}"
    )


def test_health_handler_arn_names_the_authenticated_account(
    lambda_client: Any,
    config: Dict[str, Any]
) -> None:
    function_name = config.get(
        'health_handler_function_name', 'TenULabsHealthHandler'
    )
    response = lambda_client.get_function(FunctionName=function_name)
    account_in_arn = response["Configuration"]["FunctionArn"].split(":")[4]
    assert account_in_arn == get_aws_account_id_via_cli(), (
        f"Deployed ARN names account {account_in_arn}, not the authenticated one"
    )


def test_health_handler_logs_in_text_format(health_handler_configuration: Any) -> None:
    log_format = health_handler_configuration["LoggingConfig"]["LogFormat"]
    assert log_format == "Text", (
        f"Lambda logging config should use the Text log format, got: {log_format}"
    )


def test_health_handler_describes_itself_as_the_health_endpoint(
    health_handler_configuration: Any
) -> None:
    description = health_handler_configuration.get("Description", "")
    assert description == "Health check endpoint for API", (
        f"Lambda description should name the health endpoint, got: {description}"
    )
