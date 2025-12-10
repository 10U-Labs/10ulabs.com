"""Integration tests to verify deployed IAM roles and Lambda functions use PascalCase.

These tests query AWS to validate that deployed resources follow naming conventions.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
import pytest

from naming_conventions import validate_name


class TestDeployedIAMRoleNamingConventions:
    """Tests for deployed IAM role naming conventions."""

    def test_rack_designer_lambda_role_name_is_pascalcase(self, iam_client):
        """Verify RackDesigner Lambda IAM role name uses PascalCase."""
        # Currently named TenULabs-RackDesignerLambda-Role (with dashes)
        role_name = "TenULabs-RackDesignerLambda-Role"
        try:
            response = iam_client.get_role(RoleName=role_name)
            actual_name = response['Role']['RoleName']
            error = validate_name(actual_name)
            assert error is None, (
                f"Deployed IAM role has invalid name '{actual_name}': {error}"
            )
        except iam_client.exceptions.NoSuchEntityException:
            pytest.skip(f"IAM role '{role_name}' not deployed")

    def test_rack_designer_export_role_name_is_pascalcase(self, iam_client):
        """Verify RackDesigner export IAM role name uses PascalCase."""
        # Currently named TenULabs-RackDesignerExport-Role (with dashes)
        role_name = "TenULabs-RackDesignerExport-Role"
        try:
            response = iam_client.get_role(RoleName=role_name)
            actual_name = response['Role']['RoleName']
            error = validate_name(actual_name)
            assert error is None, (
                f"Deployed IAM role has invalid name '{actual_name}': {error}"
            )
        except iam_client.exceptions.NoSuchEntityException:
            pytest.skip(f"IAM role '{role_name}' not deployed")

    def test_rack_designer_crawler_trigger_role_name_is_pascalcase(self, iam_client):
        """Verify RackDesigner crawler trigger IAM role name uses PascalCase."""
        # Currently named TenULabs-RackDesignerCrawlerTrigger-Role (with dashes)
        role_name = "TenULabs-RackDesignerCrawlerTrigger-Role"
        try:
            response = iam_client.get_role(RoleName=role_name)
            actual_name = response['Role']['RoleName']
            error = validate_name(actual_name)
            assert error is None, (
                f"Deployed IAM role has invalid name '{actual_name}': {error}"
            )
        except iam_client.exceptions.NoSuchEntityException:
            pytest.skip(f"IAM role '{role_name}' not deployed")


class TestDeployedLambdaFunctionNamingConventions:
    """Tests for deployed Lambda function naming conventions."""

    def test_rack_designer_handler_function_name_is_pascalcase(self, lambda_client):
        """Verify RackDesignerHandler Lambda function name uses PascalCase."""
        # Currently named TenULabs-RackDesignerHandler (with dash)
        function_name = "TenULabs-RackDesignerHandler"
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            actual_name = response['Configuration']['FunctionName']
            error = validate_name(actual_name)
            assert error is None, (
                f"Deployed Lambda function has invalid name '{actual_name}': {error}"
            )
        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.skip(f"Lambda function '{function_name}' not deployed")

    def test_rack_designer_export_function_name_is_pascalcase(self, lambda_client):
        """Verify RackDesigner export Lambda function name uses PascalCase."""
        # Currently named TenULabs-RackDesignerExport (with dash)
        function_name = "TenULabs-RackDesignerExport"
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            actual_name = response['Configuration']['FunctionName']
            error = validate_name(actual_name)
            assert error is None, (
                f"Deployed Lambda function has invalid name '{actual_name}': {error}"
            )
        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.skip(f"Lambda function '{function_name}' not deployed")

    def test_rack_designer_crawler_trigger_function_name_is_pascalcase(self, lambda_client):
        """Verify RackDesigner crawler trigger Lambda function name uses PascalCase."""
        # Currently named TenULabs-RackDesignerCrawlerTrigger (with dash)
        function_name = "TenULabs-RackDesignerCrawlerTrigger"
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            actual_name = response['Configuration']['FunctionName']
            error = validate_name(actual_name)
            assert error is None, (
                f"Deployed Lambda function has invalid name '{actual_name}': {error}"
            )
        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.skip(f"Lambda function '{function_name}' not deployed")
