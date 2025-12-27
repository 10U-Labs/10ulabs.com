"""Integration tests to verify deployed IAM roles and Lambda functions use PascalCase.

These tests query AWS to validate that deployed resources follow naming conventions.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
from test_fixtures.integration import create_deployed_naming_convention_tests


# pylint: disable=invalid-name
(
    TestDeployedIAMRoleNamingConventions,
    TestDeployedLambdaFunctionNamingConventions,
) = create_deployed_naming_convention_tests(
    function_name_config_key='simulation_soc_handler_function_name',
    default_function_name='TenULabsSimulationSocHandler',
    handler_display_name='SimulationSocHandler',
)
