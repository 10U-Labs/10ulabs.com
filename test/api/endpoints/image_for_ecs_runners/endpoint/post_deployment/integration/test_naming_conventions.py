"""Integration tests to verify deployed IAM roles and Lambda functions use PascalCase.

These tests query AWS to validate that deployed resources follow naming conventions.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
import pytest

from naming_conventions import validate_name


class TestDeployedIAMRoleNamingConventions:
    """Tests for deployed IAM role naming conventions."""

    def test_image_for_ecs_runners_handler_role_name_is_pascalcase(self, iam_client, config):
        """Verify ImageForEcsRunnersHandler IAM role name uses PascalCase."""
        function_name = config.get(
            'image_for_ecs_runners_handler_function_name',
            'TenULabsImageForEcsRunnersHandler'
        )
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

    def test_image_for_ecs_runners_handler_role_has_no_dashes(self, iam_client, config):
        """Verify ImageForEcsRunnersHandler IAM role name contains no dashes."""
        function_name = config.get(
            'image_for_ecs_runners_handler_function_name',
            'TenULabsImageForEcsRunnersHandler'
        )
        role_name = f"{function_name}ServiceRole"
        try:
            response = iam_client.get_role(RoleName=role_name)
            actual_name = response['Role']['RoleName']
            assert '-' not in actual_name, (
                f"Deployed IAM role '{actual_name}' contains dashes"
            )
        except iam_client.exceptions.NoSuchEntityException:
            pytest.skip(f"IAM role '{role_name}' not deployed")


class TestDeployedLambdaFunctionNamingConventions:
    """Tests for deployed Lambda function naming conventions."""

    def test_image_for_ecs_runners_handler_function_name_is_pascalcase(self, lambda_client, config):
        """Verify ImageForEcsRunnersHandler Lambda function name uses PascalCase."""
        function_name = config.get(
            'image_for_ecs_runners_handler_function_name',
            'TenULabsImageForEcsRunnersHandler'
        )
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            actual_name = response['Configuration']['FunctionName']
            error = validate_name(actual_name)
            assert error is None, (
                f"Deployed Lambda function has invalid name '{actual_name}': {error}"
            )
        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.skip(f"Lambda function '{function_name}' not deployed")

    def test_image_for_ecs_runners_handler_function_has_no_dashes(self, lambda_client, config):
        """Verify ImageForEcsRunnersHandler Lambda function name contains no dashes."""
        function_name = config.get(
            'image_for_ecs_runners_handler_function_name',
            'TenULabsImageForEcsRunnersHandler'
        )
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            actual_name = response['Configuration']['FunctionName']
            assert '-' not in actual_name, (
                f"Deployed Lambda function '{actual_name}' contains dashes"
            )
        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.skip(f"Lambda function '{function_name}' not deployed")
