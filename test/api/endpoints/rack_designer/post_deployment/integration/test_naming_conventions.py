"""Integration tests to verify deployed IAM roles and Lambda functions use PascalCase.

These tests query AWS to validate that deployed resources follow naming conventions.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
import pytest

from naming_conventions import validate_name


class TestDeployedIAMRoleNamingConventions:
    """Tests for deployed IAM role naming conventions."""

    def test_rack_designer_lambda_role_exists(self, iam_client):
        """Verify RackDesigner Lambda IAM role exists."""
        role_name = "TenULabsRackDesignerLambdaRole"
        try:
            iam_client.get_role(RoleName=role_name)
        except iam_client.exceptions.NoSuchEntityException:
            pytest.fail(f"IAM role '{role_name}' does not exist")

    def test_rack_designer_lambda_role_name_is_pascalcase(self, iam_client):
        """Verify RackDesigner Lambda IAM role name uses PascalCase."""
        role_name = "TenULabsRackDesignerLambdaRole"
        response = iam_client.get_role(RoleName=role_name)
        actual_name = response['Role']['RoleName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed IAM role has invalid name '{actual_name}': {error}"
        )

    def test_rack_designer_export_role_exists(self, iam_client):
        """Verify RackDesigner export IAM role exists."""
        role_name = "TenULabsRackDesignerExportRole"
        try:
            iam_client.get_role(RoleName=role_name)
        except iam_client.exceptions.NoSuchEntityException:
            pytest.fail(f"IAM role '{role_name}' does not exist")

    def test_rack_designer_export_role_name_is_pascalcase(self, iam_client):
        """Verify RackDesigner export IAM role name uses PascalCase."""
        role_name = "TenULabsRackDesignerExportRole"
        response = iam_client.get_role(RoleName=role_name)
        actual_name = response['Role']['RoleName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed IAM role has invalid name '{actual_name}': {error}"
        )

    def test_rack_designer_crawler_trigger_role_exists(self, iam_client):
        """Verify RackDesigner crawler trigger IAM role exists."""
        role_name = "TenULabsRackDesignerCrawlerTriggerRole"
        try:
            iam_client.get_role(RoleName=role_name)
        except iam_client.exceptions.NoSuchEntityException:
            pytest.fail(f"IAM role '{role_name}' does not exist")

    def test_rack_designer_crawler_trigger_role_name_is_pascalcase(self, iam_client):
        """Verify RackDesigner crawler trigger IAM role name uses PascalCase."""
        role_name = "TenULabsRackDesignerCrawlerTriggerRole"
        response = iam_client.get_role(RoleName=role_name)
        actual_name = response['Role']['RoleName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed IAM role has invalid name '{actual_name}': {error}"
        )


class TestDeployedLambdaFunctionNamingConventions:
    """Tests for deployed Lambda function naming conventions."""

    def test_rack_designer_handler_function_exists(self, lambda_client):
        """Verify RackDesignerHandler Lambda function exists."""
        function_name = "TenULabsRackDesignerHandler"
        try:
            lambda_client.get_function(FunctionName=function_name)
        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.fail(f"Lambda function '{function_name}' does not exist")

    def test_rack_designer_handler_function_name_is_pascalcase(self, lambda_client):
        """Verify RackDesignerHandler Lambda function name uses PascalCase."""
        function_name = "TenULabsRackDesignerHandler"
        response = lambda_client.get_function(FunctionName=function_name)
        actual_name = response['Configuration']['FunctionName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed Lambda function has invalid name '{actual_name}': {error}"
        )

    def test_rack_designer_export_function_exists(self, lambda_client):
        """Verify RackDesigner export Lambda function exists."""
        function_name = "TenULabsRackDesignerExport"
        try:
            lambda_client.get_function(FunctionName=function_name)
        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.fail(f"Lambda function '{function_name}' does not exist")

    def test_rack_designer_export_function_name_is_pascalcase(self, lambda_client):
        """Verify RackDesigner export Lambda function name uses PascalCase."""
        function_name = "TenULabsRackDesignerExport"
        response = lambda_client.get_function(FunctionName=function_name)
        actual_name = response['Configuration']['FunctionName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed Lambda function has invalid name '{actual_name}': {error}"
        )

    def test_rack_designer_crawler_trigger_function_exists(self, lambda_client):
        """Verify RackDesigner crawler trigger Lambda function exists."""
        function_name = "TenULabsRackDesignerCrawlerTrigger"
        try:
            lambda_client.get_function(FunctionName=function_name)
        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.fail(f"Lambda function '{function_name}' does not exist")

    def test_rack_designer_crawler_trigger_function_name_is_pascalcase(self, lambda_client):
        """Verify RackDesigner crawler trigger Lambda function name uses PascalCase."""
        function_name = "TenULabsRackDesignerCrawlerTrigger"
        response = lambda_client.get_function(FunctionName=function_name)
        actual_name = response['Configuration']['FunctionName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed Lambda function has invalid name '{actual_name}': {error}"
        )
