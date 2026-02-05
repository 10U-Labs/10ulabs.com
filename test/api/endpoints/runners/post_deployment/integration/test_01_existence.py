"""Layer 1: Existence tests.

Verify resources created by this deployment exist.
"""
import pytest

from test_fixtures.integration import check_iam_role_exists, check_lambda_function_exists


TERRAFORM_PATH = "src/api/endpoints/runners/"


def test_lambda_function_exists(lambda_client, lambda_function_name):
    """Verify the runners router Lambda function exists."""
    if not lambda_function_name:
        pytest.skip("lambda_function_name not available from terraform output")
    check_lambda_function_exists(lambda_client, lambda_function_name, TERRAFORM_PATH)
    assert True  # Explicit pass


def test_lambda_execution_role_exists(iam_client, lambda_role_name):
    """Verify the Lambda execution role exists."""
    check_iam_role_exists(iam_client, lambda_role_name, TERRAFORM_PATH)
    assert True  # Explicit pass


def test_handler_log_group_exists(handler_log_group):
    """Verify CloudWatch log group for Lambda handler exists."""
    assert handler_log_group["exists"], (
        f"CloudWatch log group '{handler_log_group['name']}' does not exist"
    )
