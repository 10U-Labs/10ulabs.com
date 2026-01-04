"""Layer 1: Existence - Verify resources created by this deployment exist.

These tests verify that all resources created by terraform apply exist.
"""
import pytest



class TestLambdaFunctionExists:
    """Layer 1: Verify Lambda function exists."""

    def test_ec2_images_handler_function_exists(
        self, fetched_lambda_function, handler_function_name
    ):
        """Verify RunnersEC2ImagesHandler Lambda function exists."""
        assert (
            fetched_lambda_function['Configuration']['FunctionName']
            == handler_function_name
        )

    def test_ec2_images_handler_function_has_configuration(
        self, fetched_lambda_function
    ):
        """Verify Lambda function has Configuration section."""
        assert 'Configuration' in fetched_lambda_function


class TestIAMRoleExists:
    """Layer 1: Verify IAM role exists."""

    def test_ec2_images_handler_role_exists(
        self, fetched_iam_role, handler_role_name
    ):
        """Verify RunnersEC2ImagesHandler IAM role exists."""
        assert fetched_iam_role['Role']['RoleName'] == handler_role_name

    def test_ec2_images_handler_role_has_arn(
        self, fetched_iam_role
    ):
        """Verify IAM role has an ARN."""
        assert fetched_iam_role['Role']['Arn'].startswith('arn:aws:iam::')


def test_ec2_images_handler_log_group_exists(handler_log_group):
    """Verify RunnersEC2ImagesHandler CloudWatch log group exists."""
    assert handler_log_group["exists"], (
        f"RunnersEC2Images log group '{handler_log_group['name']}' does not exist"
    )
