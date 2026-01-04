"""Layer 1: Existence tests for rack designer endpoint.

Verify that resources created by this deployment exist.

Three-layer testing model:
- Layer 1: Existence - Resources were created
"""
import pytest
from botocore.exceptions import ClientError




class TestResourceExistence:
    """Layer 1: Verify core resources were created."""

    def test_handler_lambda_exists(self, lambda_client, handler_function_name):
        """Verify rack designer handler Lambda function exists."""
        try:
            lambda_client.get_function(FunctionName=handler_function_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Lambda function '{handler_function_name}' does not exist"
                )
            raise
        assert True  # Explicit pass

    def test_handler_iam_role_exists(self, iam_client, handler_role_name):
        """Verify rack designer handler IAM role exists."""
        try:
            iam_client.get_role(RoleName=handler_role_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(f"IAM role '{handler_role_name}' does not exist")
            raise
        assert True  # Explicit pass

    def test_configurations_table_exists(
        self, dynamodb_client, configurations_table_name
    ):
        """Verify rack designer configurations DynamoDB table exists."""
        try:
            dynamodb_client.describe_table(TableName=configurations_table_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"DynamoDB table '{configurations_table_name}' does not exist"
                )
            raise
        assert True  # Explicit pass

    def test_handler_log_group_exists(self, handler_log_group):
        """Verify rack designer handler CloudWatch log group exists."""
        assert handler_log_group["exists"], (
            f"CloudWatch log group '{handler_log_group['name']}' does not exist"
        )
