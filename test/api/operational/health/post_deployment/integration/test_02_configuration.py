"""Layer 2: Configuration tests for health endpoint post-deployment.

Tests that resources have correct settings. Assumes existence tests passed.
These tests verify that resources created by THIS workflow are configured correctly.

Three-layer testing model:
- Layer 2: Configuration - Resources configured correctly
"""


from test_fixtures.integration import (
    create_lambda_configuration_tests,
    create_log_group_configuration_tests,
    create_naming_convention_tests,
)




TestLambdaConfiguration = create_lambda_configuration_tests(
    function_name_config_key="health_handler_function_name",
    default_function_name="TenULabsHealthHandler",
)

TestCloudWatchLogsConfiguration = create_log_group_configuration_tests(
    log_group_fixture="health_handler_log_group",
    expected_retention=7,
)

TestNamingConventions = create_naming_convention_tests(
    function_name_config_key="health_handler_function_name",
    default_function_name="TenULabsHealthHandler",
)


class TestHealthLambdaTimeout:  # pylint: disable=too-few-public-methods
    """Health-specific Lambda timeout configuration test."""

    def test_handler_has_10_second_timeout(self, lambda_client, config):
        """Verify Lambda function has 10 second timeout."""
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        response = lambda_client.get_function(FunctionName=function_name)
        timeout = response["Configuration"]["Timeout"]
        assert timeout == 10, (
            f"Lambda timeout should be 10 seconds, got: {timeout}"
        )
