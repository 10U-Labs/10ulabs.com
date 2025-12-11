"""Integration tests to verify deployed IAM roles and Lambda functions use PascalCase.

These tests query AWS to validate that deployed resources follow naming conventions.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
import pytest

from naming_conventions import validate_name


def test_health_handler_role_name_is_pascalcase(iam_client, config):
    """Verify HealthHandler IAM role name uses PascalCase."""
    function_name = config.get('health_handler_function_name', 'TenULabsHealthHandler')
    role_name = f"{function_name}ServiceRole"
    try:
        response = iam_client.get_role(RoleName=role_name)
        actual_name = response['Role']['RoleName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed IAM role has invalid name '{actual_name}': {error}"
        )
    except iam_client.exceptions.NoSuchEntityException:
        pytest.skip(f"IAM role '{role_name}' not deployed")


def test_health_handler_function_name_is_pascalcase(lambda_client, config):
    """Verify HealthHandler Lambda function name uses PascalCase."""
    function_name = config.get('health_handler_function_name', 'TenULabsHealthHandler')
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        actual_name = response['Configuration']['FunctionName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed Lambda function has invalid name '{actual_name}': {error}"
        )
    except lambda_client.exceptions.ResourceNotFoundException:
        pytest.skip(f"Lambda function '{function_name}' not deployed")
