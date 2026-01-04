"""Layer 1: Existence tests for sessions endpoint post-deployment.

Existence tests verify that resources created by terraform apply exist.
No configuration checks - just existence.
"""
import pytest
from botocore.exceptions import ClientError



class TestLambdaExistence:
    """Tests for Lambda function existence."""

    def test_sessions_handler_lambda_exists(self, lambda_client, sessions_config):
        """Verify sessions handler Lambda exists."""
        response = lambda_client.get_function(
            FunctionName=sessions_config["handler_function_name"]
        )
        assert response["Configuration"]["FunctionName"] == sessions_config["handler_function_name"]

    def test_sessions_export_lambda_exists(self, lambda_client, sessions_config):
        """Verify sessions export Lambda exists."""
        response = lambda_client.get_function(
            FunctionName=sessions_config["export_function_name"]
        )
        assert response["Configuration"]["FunctionName"] == sessions_config["export_function_name"]

    def test_sessions_crawler_trigger_lambda_exists(self, lambda_client, sessions_config):
        """Verify sessions crawler trigger Lambda exists."""
        response = lambda_client.get_function(
            FunctionName=sessions_config["crawler_trigger_function_name"]
        )
        assert response["Configuration"]["FunctionName"] == sessions_config["crawler_trigger_function_name"]


class TestDynamoDbExistence:
    """Tests for DynamoDB table existence."""

    def test_session_events_dynamodb_table_exists(self, dynamodb_client, sessions_config):
        """Verify session events DynamoDB table exists."""
        response = dynamodb_client.describe_table(
            TableName=sessions_config["dynamodb_table_name"]
        )
        assert response["Table"]["TableName"] == sessions_config["dynamodb_table_name"]


class TestS3Existence:
    """Tests for S3 bucket existence."""

    def test_analytics_s3_bucket_exists(self, s3_client, sessions_config):
        """Verify analytics S3 bucket exists."""
        response = s3_client.head_bucket(Bucket=sessions_config["s3_bucket_name"])
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


class TestGlueExistence:
    """Tests for Glue resources existence."""

    def test_glue_database_exists(self, glue_client, sessions_config):
        """Verify Glue catalog database exists."""
        response = glue_client.get_database(Name=sessions_config["glue_database_name"])
        assert response["Database"]["Name"] == sessions_config["glue_database_name"]

    def test_glue_crawler_exists(self, glue_client, sessions_config):
        """Verify Glue crawler exists."""
        response = glue_client.get_crawler(Name=sessions_config["glue_crawler_name"])
        assert response["Crawler"]["Name"] == sessions_config["glue_crawler_name"]


class TestCloudWatchLogsExistence:
    """Tests for CloudWatch Log Group existence."""

    def test_handler_log_group_exists(self, logs_client, sessions_config):
        """Verify handler CloudWatch log group exists."""
        response = logs_client.describe_log_groups(
            logGroupNamePrefix=sessions_config["handler_log_group"]
        )
        log_groups = [lg["logGroupName"] for lg in response["logGroups"]]
        assert sessions_config["handler_log_group"] in log_groups

    def test_export_log_group_exists(self, logs_client, sessions_config):
        """Verify export CloudWatch log group exists."""
        response = logs_client.describe_log_groups(
            logGroupNamePrefix=sessions_config["export_log_group"]
        )
        log_groups = [lg["logGroupName"] for lg in response["logGroups"]]
        assert sessions_config["export_log_group"] in log_groups

    def test_crawler_trigger_log_group_exists(self, logs_client, sessions_config):
        """Verify crawler trigger log group exists."""
        response = logs_client.describe_log_groups(
            logGroupNamePrefix=sessions_config["crawler_trigger_log_group"]
        )
        log_groups = [lg["logGroupName"] for lg in response["logGroups"]]
        assert sessions_config["crawler_trigger_log_group"] in log_groups


class TestBackupExistence:
    """Tests for AWS Backup resource existence."""

    def test_backup_vault_exists(self, backup_client, sessions_config):
        """Verify AWS Backup vault exists."""
        response = backup_client.describe_backup_vault(
            BackupVaultName=sessions_config["backup_vault_name"]
        )
        assert response["BackupVaultName"] == sessions_config["backup_vault_name"]

    def test_backup_plan_exists(self, backup_client, sessions_config):
        """Verify backup plan exists."""
        response = backup_client.list_backup_plans()
        plan_names = [p["BackupPlanName"] for p in response["BackupPlansList"]]
        assert sessions_config["backup_plan_name"] in plan_names


class TestEventBridgeExistence:
    """Tests for EventBridge resource existence."""

    def test_eventbridge_scheduler_exists(self, scheduler_client, sessions_config):
        """Verify EventBridge scheduler exists."""
        response = scheduler_client.get_schedule(
            Name=sessions_config["scheduler_name"]
        )
        assert response["Name"] == sessions_config["scheduler_name"]

    def test_eventbridge_export_completed_rule_exists(self, events_client, sessions_config):
        """Verify EventBridge rule exists."""
        response = events_client.describe_rule(
            Name=sessions_config["eventbridge_rule_name"]
        )
        assert response["Name"] == sessions_config["eventbridge_rule_name"]


class TestIamRoleExistence:
    """Tests for IAM role existence."""

    def test_sessions_handler_iam_role_exists(self, iam_client, sessions_config):
        """Verify sessions handler IAM role exists."""
        response = iam_client.get_role(RoleName=sessions_config["handler_role_name"])
        assert response["Role"]["RoleName"] == sessions_config["handler_role_name"]

    def test_sessions_export_iam_role_exists(self, iam_client, sessions_config):
        """Verify sessions export IAM role exists."""
        response = iam_client.get_role(RoleName=sessions_config["export_role_name"])
        assert response["Role"]["RoleName"] == sessions_config["export_role_name"]

    def test_sessions_crawler_trigger_iam_role_exists(self, iam_client, sessions_config):
        """Verify sessions crawler trigger IAM role exists."""
        response = iam_client.get_role(RoleName=sessions_config["crawler_trigger_role_name"])
        assert response["Role"]["RoleName"] == sessions_config["crawler_trigger_role_name"]

    def test_glue_crawler_iam_role_exists(self, iam_client, sessions_config):
        """Verify Glue crawler IAM role exists."""
        response = iam_client.get_role(RoleName=sessions_config["glue_crawler_role_name"])
        assert response["Role"]["RoleName"] == sessions_config["glue_crawler_role_name"]

    def test_scheduler_iam_role_exists(self, iam_client, sessions_config):
        """Verify scheduler IAM role exists."""
        response = iam_client.get_role(RoleName=sessions_config["scheduler_role_name"])
        assert response["Role"]["RoleName"] == sessions_config["scheduler_role_name"]

    def test_backup_iam_role_exists(self, iam_client, sessions_config):
        """Verify backup IAM role exists."""
        response = iam_client.get_role(RoleName=sessions_config["backup_role_name"])
        assert response["Role"]["RoleName"] == sessions_config["backup_role_name"]
