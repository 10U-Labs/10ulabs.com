from typing import Any

import pytest
from botocore.exceptions import ClientError


class TestResourceExistence:
    def test_handler_lambda_exists(self, lambda_client: Any, handler_function_name: str) -> None:
        try:
            lambda_client.get_function(FunctionName=handler_function_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Lambda function '{handler_function_name}' does not exist"
                )
            raise
        assert True

    def test_handler_iam_role_exists(self, iam_client: Any, handler_role_name: str) -> None:
        try:
            iam_client.get_role(RoleName=handler_role_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(f"IAM role '{handler_role_name}' does not exist")
            raise
        assert True

    def test_configurations_table_exists(
        self, dynamodb_client: Any, configurations_table_name: str
    ) -> None:
        try:
            dynamodb_client.describe_table(TableName=configurations_table_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"DynamoDB table '{configurations_table_name}' does not exist"
                )
            raise
        assert True

    def test_handler_log_group_exists(self, handler_log_group: Any) -> None:
        assert handler_log_group["exists"], (
            f"CloudWatch log group '{handler_log_group['name']}' does not exist"
        )
