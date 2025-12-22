"""Layer 1: Existence tests.

Verify resources created by this deployment exist.
"""
import pytest

pytestmark = pytest.mark.layer(1)


def test_lambda_function_exists(lambda_function):
    """Verify the ImageForEcsRunners Lambda function exists."""
    assert lambda_function is not None


def test_lambda_function_has_arn(lambda_function):
    """Verify the Lambda function has an ARN."""
    assert "FunctionArn" in lambda_function


def test_lambda_function_has_role(lambda_function):
    """Verify the Lambda function has a Role configured."""
    assert "Role" in lambda_function
