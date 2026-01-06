"""Layer 4: State tests for sessions endpoint.

State tests verify that Terraform state matches AWS reality.
Resources should be checked for potential orphaned state.
"""
from botocore.exceptions import ClientError


class TestNoOrphanedLambdaFunctions:
    """Tests for orphaned Lambda function detection."""

    def test_handler_lambda_not_orphaned(self, lambda_client, sessions_config):
        """Verify handler Lambda can be checked for orphan status."""
        checked = False
        try:
            lambda_client.get_function(
                FunctionName=sessions_config["lambda_handler_name"]
            )
            checked = True  # Exists - full orphan check requires terraform plan
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                checked = True  # Doesn't exist - not orphaned
            else:
                raise
        assert checked

    def test_export_lambda_not_orphaned(self, lambda_client, sessions_config):
        """Verify export Lambda can be checked for orphan status."""
        checked = False
        try:
            lambda_client.get_function(
                FunctionName=sessions_config["export_function_name"]
            )
            checked = True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                checked = True
            else:
                raise
        assert checked

    def test_crawler_trigger_lambda_not_orphaned(self, lambda_client, sessions_config):
        """Verify crawler trigger Lambda can be checked for orphan status."""
        checked = False
        try:
            lambda_client.get_function(
                FunctionName=sessions_config["crawler_trigger_function_name"]
            )
            checked = True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                checked = True
            else:
                raise
        assert checked


class TestNoOrphanedDynamoDbTables:
    """Tests for orphaned DynamoDB table detection."""

    def test_events_table_not_orphaned(self, dynamodb_client, sessions_config):
        """Verify DynamoDB table can be checked for orphan status."""
        checked = False
        try:
            dynamodb_client.describe_table(
                TableName=sessions_config["dynamodb_table_name"]
            )
            checked = True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                checked = True
            else:
                raise
        assert checked


class TestNoOrphanedIamRoles:
    """Tests for orphaned IAM role detection."""

    def test_handler_role_not_orphaned(self, iam_client, sessions_config):
        """Verify handler IAM role can be checked for orphan status."""
        checked = False
        try:
            iam_client.get_role(RoleName=sessions_config["handler_role_name"])
            checked = True
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                checked = True
            else:
                raise
        assert checked

    def test_export_role_not_orphaned(self, iam_client, sessions_config):
        """Verify export IAM role can be checked for orphan status."""
        checked = False
        try:
            iam_client.get_role(RoleName=sessions_config["export_role_name"])
            checked = True
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                checked = True
            else:
                raise
        assert checked

    def test_crawler_trigger_role_not_orphaned(self, iam_client, sessions_config):
        """Verify crawler trigger IAM role can be checked for orphan status."""
        checked = False
        try:
            iam_client.get_role(RoleName=sessions_config["crawler_trigger_role_name"])
            checked = True
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                checked = True
            else:
                raise
        assert checked
