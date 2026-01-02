"""Integration tests to verify deployed IAM roles and Lambda functions use PascalCase.

These tests query AWS to validate that deployed resources follow naming conventions.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
from test_fixtures.integration import create_deployed_naming_convention_tests


# Use factory for naming convention tests - assigns to class names
_naming_tests = create_deployed_naming_convention_tests(
    function_name_config_key='simulation_soc_handler_function_name',
    default_function_name='TenULabsSimulationSocHandler',
    handler_display_name='SimulationSocHandler',
)
TestDeployedIAMRoleNamingConventions = _naming_tests[0]
TestDeployedLambdaFunctionNamingConventions = _naming_tests[1]
