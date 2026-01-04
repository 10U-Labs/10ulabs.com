"""Layer 2: Configuration - Verify resources are configured correctly.

These tests verify that all resources created by terraform apply are
configured correctly. Assumes existence (Layer 1) has passed.
"""
import pytest

from naming_conventions import validate_name



class TestLambdaFunctionConfiguration:
    """Layer 2: Verify Lambda function is configured correctly."""

    def test_ec2_images_handler_function_name_is_pascalcase(
        self, fetched_lambda_function
    ):
        """Verify RunnersEC2ImagesHandler Lambda function name uses PascalCase."""
        actual_name = fetched_lambda_function['Configuration']['FunctionName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed Lambda function has invalid name '{actual_name}': {error}"
        )

    def test_ec2_images_handler_has_runtime(
        self, fetched_lambda_function
    ):
        """Verify Lambda function has a runtime configured."""
        assert 'Runtime' in fetched_lambda_function['Configuration']


class TestIAMRoleConfiguration:
    """Layer 2: Verify IAM role is configured correctly."""

    def test_ec2_images_handler_role_name_is_pascalcase(
        self, fetched_iam_role
    ):
        """Verify RunnersEC2ImagesHandler IAM role name uses PascalCase."""
        actual_name = fetched_iam_role['Role']['RoleName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed IAM role has invalid name '{actual_name}': {error}"
        )

    def test_ec2_images_handler_role_has_assume_role_policy(
        self, fetched_iam_role
    ):
        """Verify IAM role has an assume role policy document."""
        assert 'AssumeRolePolicyDocument' in fetched_iam_role['Role']


class TestRunnersEC2ImagesLogGroupConfiguration:
    """Layer 2: Verify RunnersEC2Images log group is configured correctly."""

    def test_ec2_images_log_group_has_retention(self, handler_log_group):
        """Verify RunnersEC2Images log group has retention configured."""
        assert handler_log_group["retention"] is not None, (
            f"RunnersEC2Images log group '{handler_log_group['name']}' "
            "should have retention set"
        )

    def test_ec2_images_log_group_retention_is_7_days(
        self, handler_log_group
    ):
        """Verify RunnersEC2Images log group uses 7-day retention."""
        retention = handler_log_group["retention"]
        assert retention == 7, (
            f"RunnersEC2Images log group retention is {retention} days, expected 7"
        )
