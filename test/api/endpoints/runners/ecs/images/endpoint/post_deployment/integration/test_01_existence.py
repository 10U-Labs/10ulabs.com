"""Layer 1: Existence tests.

Verify resources created by this deployment exist.
"""
import pytest


class TestLambdaFunctionExistence:
    """Verify Lambda function exists."""

    def test_lambda_function_exists(self, lambda_function):
        """Verify the ImageForEcsRunners Lambda function exists."""
        assert lambda_function is not None

    def test_lambda_function_has_arn(self, lambda_function):
        """Verify the Lambda function has an ARN."""
        assert "FunctionArn" in lambda_function

    def test_lambda_function_has_role(self, lambda_function):
        """Verify the Lambda function has a Role configured."""
        assert "Role" in lambda_function


class TestIAMRoleExistence:
    """Verify IAM role exists."""

    def test_lambda_service_role_exists(self, lambda_role):
        """Verify the Lambda service IAM role exists."""
        assert lambda_role is not None

    def test_lambda_service_role_has_arn(self, lambda_role):
        """Verify the Lambda service role has an ARN."""
        assert "Arn" in lambda_role


class TestCloudWatchLogGroupExistence:
    """Verify CloudWatch log group exists."""

    def test_handler_log_group_exists(self, handler_log_group):
        """Verify CloudWatch log group for Lambda handler exists."""
        assert handler_log_group["exists"], (
            f"CloudWatch log group '{handler_log_group['name']}' does not exist"
        )
