"""Integration tests to verify deployed IAM roles and Lambda functions use PascalCase.

These tests query AWS to validate that deployed resources follow naming conventions.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
import pytest

from naming_conventions import validate_name


class TestDeployedIAMRoleNamingConventions:
    """Tests for deployed IAM role naming conventions."""

    def test_ec2_runner_lambda_role_name_is_pascalcase(self, iam_client):
        """Verify EC2 runner Lambda IAM role name uses PascalCase."""
        # Currently named TenULabs-EC2RunnerLambda-Role (with dashes)
        role_name = "TenULabs-EC2RunnerLambda-Role"
        try:
            response = iam_client.get_role(RoleName=role_name)
            actual_name = response['Role']['RoleName']
            error = validate_name(actual_name)
            assert error is None, (
                f"Deployed IAM role has invalid name '{actual_name}': {error}"
            )
        except iam_client.exceptions.NoSuchEntityException:
            pytest.skip(f"IAM role '{role_name}' not deployed")

    def test_github_self_hosted_runner_role_name_is_pascalcase(self, iam_client):
        """Verify GitHub self-hosted runner IAM role name uses PascalCase."""
        role_name = "GitHubSelfHostedRunnerEC2Role"
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

    def test_ec2_runner_handler_function_name_is_pascalcase(self, lambda_client, config):
        """Verify EC2RunnerHandler Lambda function name uses PascalCase."""
        function_name = config.get('ec2_runner_handler_function_name', 'TenULabsEC2RunnerHandler')
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            actual_name = response['Configuration']['FunctionName']
            error = validate_name(actual_name)
            assert error is None, (
                f"Deployed Lambda function has invalid name '{actual_name}': {error}"
            )
        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.skip(f"Lambda function '{function_name}' not deployed")

    def test_ec2_runner_handler_function_name_has_no_dashes(self, lambda_client, config):
        """Verify EC2RunnerHandler Lambda function name has no dashes."""
        function_name = config.get('ec2_runner_handler_function_name', 'TenULabsEC2RunnerHandler')
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            actual_name = response['Configuration']['FunctionName']
            assert '-' not in actual_name, (
                f"Deployed Lambda function has dashes in name '{actual_name}'"
            )
        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.skip(f"Lambda function '{function_name}' not deployed")
