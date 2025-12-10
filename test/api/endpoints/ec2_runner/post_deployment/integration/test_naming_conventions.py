"""Integration tests to verify deployed IAM roles and Lambda functions use PascalCase.

These tests query AWS to validate that deployed resources follow naming conventions.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
from naming_conventions import validate_name


class TestDeployedIAMRoleNamingConventions:
    """Tests for deployed IAM role naming conventions."""

    def test_ec2_runner_lambda_role_name_is_pascalcase(self, lambda_role_name):
        """Verify EC2 runner Lambda IAM role name uses PascalCase."""
        error = validate_name(lambda_role_name)
        assert error is None, (
            f"IAM role has invalid name '{lambda_role_name}': {error}"
        )

    def test_ec2_runner_role_name_is_pascalcase(self, ec2_runner_role_name):
        """Verify EC2 runner IAM role name uses PascalCase."""
        error = validate_name(ec2_runner_role_name)
        assert error is None, (
            f"IAM role has invalid name '{ec2_runner_role_name}': {error}"
        )


class TestDeployedLambdaFunctionNamingConventions:
    """Tests for deployed Lambda function naming conventions."""

    def test_ec2_runner_handler_function_name_is_pascalcase(self, lambda_function_name):
        """Verify EC2RunnerHandler Lambda function name uses PascalCase."""
        error = validate_name(lambda_function_name)
        assert error is None, (
            f"Lambda function has invalid name '{lambda_function_name}': {error}"
        )

    def test_ec2_runner_handler_function_name_has_no_dashes(self, lambda_function_name):
        """Verify EC2RunnerHandler Lambda function name has no dashes."""
        assert '-' not in lambda_function_name, (
            f"Lambda function has dashes in name '{lambda_function_name}'"
        )
