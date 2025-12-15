"""Integration tests to verify deployed IAM roles and Lambda functions use PascalCase.

These tests query AWS to validate that deployed resources follow naming conventions.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
import pytest

from naming_conventions import validate_name


class TestDeployedIAMRoleNamingConventions:
    """Tests for deployed IAM role naming conventions."""

    def test_agent_creator_role_exists(self, iam_client):
        """Verify AgentCreator IAM role exists."""
        role_name = "TenULabsAgentCreatorRole"
        try:
            iam_client.get_role(RoleName=role_name)
        except iam_client.exceptions.NoSuchEntityException:
            pytest.fail(f"IAM role '{role_name}' does not exist")

    def test_agent_creator_role_name_is_pascalcase(self, iam_client):
        """Verify AgentCreator IAM role name uses PascalCase."""
        role_name = "TenULabsAgentCreatorRole"
        response = iam_client.get_role(RoleName=role_name)
        actual_name = response['Role']['RoleName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed IAM role has invalid name '{actual_name}': {error}"
        )


class TestDeployedLambdaFunctionNamingConventions:
    """Tests for deployed Lambda function naming conventions."""

    def test_agent_creator_function_exists(self, lambda_client):
        """Verify AgentCreator Lambda function exists."""
        function_name = "TenULabsAgentCreator"
        try:
            lambda_client.get_function(FunctionName=function_name)
        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.fail(f"Lambda function '{function_name}' does not exist")

    def test_agent_creator_function_name_is_pascalcase(self, lambda_client):
        """Verify AgentCreator Lambda function name uses PascalCase."""
        function_name = "TenULabsAgentCreator"
        response = lambda_client.get_function(FunctionName=function_name)
        actual_name = response['Configuration']['FunctionName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed Lambda function has invalid name '{actual_name}': {error}"
        )
