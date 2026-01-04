"""Layer 1: Existence tests for rack designer endpoint.

Verify that resources created by this deployment exist.

Three-layer testing model:
- Layer 1: Existence - Resources were created
"""
import pytest
from botocore.exceptions import ClientError




class TestLambdaExistence:
    """Layer 1: Verify Lambda functions were created."""

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

    def test_export_lambda_exists(self, lambda_client, export_function_name):
        """Verify rack designer export Lambda function exists."""
        try:
            lambda_client.get_function(FunctionName=export_function_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Lambda function '{export_function_name}' does not exist"
                )
            raise

    def test_crawler_trigger_lambda_exists(
        self, lambda_client, crawler_trigger_function_name
    ):
        """Verify rack designer crawler trigger Lambda function exists."""
        try:
            lambda_client.get_function(FunctionName=crawler_trigger_function_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Lambda function '{crawler_trigger_function_name}' does not exist"
                )
            raise


class TestIAMRoleExistence:
    """Layer 1: Verify IAM roles were created."""

    def test_handler_iam_role_exists(self, iam_client, handler_role_name):
        """Verify rack designer handler IAM role exists."""
        try:
            iam_client.get_role(RoleName=handler_role_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(f"IAM role '{handler_role_name}' does not exist")
            raise

    def test_export_iam_role_exists(self, iam_client, export_role_name):
        """Verify rack designer export IAM role exists."""
        try:
            iam_client.get_role(RoleName=export_role_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(f"IAM role '{export_role_name}' does not exist")
            raise

    def test_crawler_trigger_iam_role_exists(
        self, iam_client, crawler_trigger_role_name
    ):
        """Verify rack designer crawler trigger IAM role exists."""
        try:
            iam_client.get_role(RoleName=crawler_trigger_role_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(f"IAM role '{crawler_trigger_role_name}' does not exist")
            raise

    def test_glue_crawler_iam_role_exists(self, iam_client, glue_crawler_role_name):
        """Verify rack designer Glue crawler IAM role exists."""
        try:
            iam_client.get_role(RoleName=glue_crawler_role_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(f"IAM role '{glue_crawler_role_name}' does not exist")
            raise

    def test_scheduler_iam_role_exists(self, iam_client, scheduler_role_name):
        """Verify rack designer scheduler IAM role exists."""
        try:
            iam_client.get_role(RoleName=scheduler_role_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(f"IAM role '{scheduler_role_name}' does not exist")
            raise


class TestDynamoDBAndCloudWatchExistence:
    """Layer 1: Verify DynamoDB tables and CloudWatch log groups were created."""

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

    def test_events_table_exists(self, dynamodb_client, events_table_name):
        """Verify rack designer events DynamoDB table exists."""
        try:
            dynamodb_client.describe_table(TableName=events_table_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(f"DynamoDB table '{events_table_name}' does not exist")
            raise

    def test_handler_log_group_exists(self, handler_log_group):
        """Verify rack designer handler CloudWatch log group exists."""
        assert handler_log_group["exists"], (
            f"CloudWatch log group '{handler_log_group['name']}' does not exist"
        )
