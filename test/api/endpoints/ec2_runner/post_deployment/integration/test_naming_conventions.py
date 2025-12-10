"""Integration tests to verify deployed IAM roles and Lambda functions use PascalCase.

These tests query AWS to validate that deployed resources follow naming conventions.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
from naming_conventions import validate_name


class TestDeployedNamingConventions:
    """Tests for deployed resource naming conventions."""

    def test_ec2_runner_lambda_role_name_is_pascalcase(
        self, iam_client, lambda_role_name
    ):
        """Verify EC2 runner Lambda IAM role name uses PascalCase."""
        response = iam_client.get_role(RoleName=lambda_role_name)
        actual_name = response['Role']['RoleName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed IAM role has invalid name '{actual_name}': {error}"
        )

    def test_ec2_runner_role_name_is_pascalcase(
        self, iam_client, ec2_runner_role_name
    ):
        """Verify EC2 runner IAM role name uses PascalCase."""
        response = iam_client.get_role(RoleName=ec2_runner_role_name)
        actual_name = response['Role']['RoleName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed IAM role has invalid name '{actual_name}': {error}"
        )

    def test_ec2_runner_handler_function_name_is_pascalcase(
        self, lambda_client, lambda_function_name
    ):
        """Verify EC2RunnerHandler Lambda function name uses PascalCase."""
        response = lambda_client.get_function(FunctionName=lambda_function_name)
        actual_name = response['Configuration']['FunctionName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed Lambda function has invalid name '{actual_name}': {error}"
        )
