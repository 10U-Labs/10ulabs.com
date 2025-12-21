"""Layer 1: Existence tests.

Verify resources created by this deployment exist.
"""
import pytest
from botocore.exceptions import ClientError

pytestmark = pytest.mark.layer(1)


def test_lambda_function_exists(lambda_client, lambda_function_name):
    """Verify the EC2 runner handler Lambda function exists."""
    try:
        response = lambda_client.get_function(FunctionName=lambda_function_name)
        assert response["Configuration"]["FunctionName"] == lambda_function_name
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            pytest.fail(
                f"Lambda function '{lambda_function_name}' does not exist. "
                "Run terraform apply in src/api/endpoints/ec2_runner/"
            )
        raise


def test_lambda_execution_role_exists(iam_client, lambda_role_name):
    """Verify the Lambda execution role exists."""
    try:
        response = iam_client.get_role(RoleName=lambda_role_name)
        assert response.get("Role") is not None
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            pytest.fail(
                f"Lambda execution role '{lambda_role_name}' does not exist. "
                "Run terraform apply in src/api/endpoints/ec2_runner/"
            )
        raise


def test_ec2_runner_role_exists(iam_client, ec2_runner_role_name):
    """Verify the EC2 runner IAM role exists."""
    try:
        response = iam_client.get_role(RoleName=ec2_runner_role_name)
        assert response.get("Role") is not None
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            pytest.fail(
                f"EC2 runner role '{ec2_runner_role_name}' does not exist. "
                "Run terraform apply in src/api/endpoints/ec2_runner/"
            )
        raise
