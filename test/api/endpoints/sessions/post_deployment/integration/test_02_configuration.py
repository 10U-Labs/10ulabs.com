"""Layer 2: Configuration tests for sessions endpoint post-deployment.

Configuration tests verify that resources have correct settings.
Assumes existence tests passed.
"""
import pytest
from botocore.exceptions import ClientError

pytestmark = pytest.mark.layer(2)


class TestHandlerLambdaConfiguration:
    """Tests for handler Lambda configuration."""

    def test_handler_lambda_has_10_second_timeout(self, lambda_client, sessions_config):
        """Verify handler Lambda timeout is 10 seconds."""
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["handler_function_name"]
        )
        assert response["Timeout"] == 10

    def test_handler_lambda_has_128mb_memory(self, lambda_client, sessions_config):
        """Verify handler Lambda memory is 128MB."""
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["handler_function_name"]
        )
        assert response["MemorySize"] == 128

    def test_handler_lambda_uses_arm64_architecture(self, lambda_client, sessions_config):
        """Verify handler Lambda uses arm64 architecture."""
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["handler_function_name"]
        )
        assert "arm64" in response["Architectures"]

    def test_handler_lambda_uses_python313_runtime(self, lambda_client, sessions_config):
        """Verify handler Lambda uses Python 3.13 runtime."""
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["handler_function_name"]
        )
        assert response["Runtime"] == "python3.13"

    def test_handler_lambda_has_session_events_table_env_var(self, lambda_client, sessions_config):
        """Verify handler has SESSION_EVENTS_TABLE environment variable."""
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["handler_function_name"]
        )
        env_vars = response.get("Environment", {}).get("Variables", {})
        assert "SESSION_EVENTS_TABLE" in env_vars


class TestExportLambdaConfiguration:
    """Tests for export Lambda configuration."""

    def test_export_lambda_has_30_second_timeout(self, lambda_client, sessions_config):
        """Verify export Lambda timeout is 30 seconds."""
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["export_function_name"]
        )
        assert response["Timeout"] == 30

    def test_export_lambda_has_dynamodb_table_arn_env_var(self, lambda_client, sessions_config):
        """Verify export has DYNAMODB_TABLE_ARN environment variable."""
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["export_function_name"]
        )
        env_vars = response.get("Environment", {}).get("Variables", {})
        assert "DYNAMODB_TABLE_ARN" in env_vars

    def test_export_lambda_has_s3_bucket_env_var(self, lambda_client, sessions_config):
        """Verify export has S3_BUCKET environment variable."""
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["export_function_name"]
        )
        env_vars = response.get("Environment", {}).get("Variables", {})
        assert "S3_BUCKET" in env_vars

    def test_export_lambda_has_s3_prefix_env_var(self, lambda_client, sessions_config):
        """Verify export has S3_PREFIX environment variable."""
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["export_function_name"]
        )
        env_vars = response.get("Environment", {}).get("Variables", {})
        assert "S3_PREFIX" in env_vars


class TestCrawlerTriggerLambdaConfiguration:
    """Tests for crawler trigger Lambda configuration."""

    def test_crawler_trigger_lambda_has_30_second_timeout(self, lambda_client, sessions_config):
        """Verify crawler trigger Lambda timeout is 30 seconds."""
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["crawler_trigger_function_name"]
        )
        assert response["Timeout"] == 30

    def test_crawler_trigger_lambda_has_crawler_name_env_var(self, lambda_client, sessions_config):
        """Verify crawler trigger has CRAWLER_NAME environment variable."""
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["crawler_trigger_function_name"]
        )
        env_vars = response.get("Environment", {}).get("Variables", {})
        assert "CRAWLER_NAME" in env_vars


class TestDynamoDbConfiguration:
    """Tests for DynamoDB table configuration."""

    def test_dynamodb_table_has_pay_per_request_billing(self, dynamodb_client, sessions_config):
        """Verify DynamoDB table uses PAY_PER_REQUEST billing mode."""
        response = dynamodb_client.describe_table(
            TableName=sessions_config["dynamodb_table_name"]
        )
        assert response["Table"]["BillingModeSummary"]["BillingMode"] == "PAY_PER_REQUEST"

    def test_dynamodb_table_has_point_in_time_recovery(self, dynamodb_client, sessions_config):
        """Verify DynamoDB table has point-in-time recovery enabled."""
        response = dynamodb_client.describe_continuous_backups(
            TableName=sessions_config["dynamodb_table_name"]
        )
        pitr = response["ContinuousBackupsDescription"]["PointInTimeRecoveryDescription"]
        assert pitr["PointInTimeRecoveryStatus"] == "ENABLED"

    def test_dynamodb_table_has_session_id_hash_key(self, dynamodb_client, sessions_config):
        """Verify DynamoDB table hash key is session_id."""
        response = dynamodb_client.describe_table(
            TableName=sessions_config["dynamodb_table_name"]
        )
        key_schema = response["Table"]["KeySchema"]
        hash_key = next(k for k in key_schema if k["KeyType"] == "HASH")
        assert hash_key["AttributeName"] == "session_id"

    def test_dynamodb_table_has_timestamp_range_key(self, dynamodb_client, sessions_config):
        """Verify DynamoDB table range key is timestamp."""
        response = dynamodb_client.describe_table(
            TableName=sessions_config["dynamodb_table_name"]
        )
        key_schema = response["Table"]["KeySchema"]
        range_key = next(k for k in key_schema if k["KeyType"] == "RANGE")
        assert range_key["AttributeName"] == "timestamp"

    def test_dynamodb_table_has_event_type_gsi(self, dynamodb_client, sessions_config):
        """Verify DynamoDB table has event_type GSI."""
        response = dynamodb_client.describe_table(
            TableName=sessions_config["dynamodb_table_name"]
        )
        gsis = response["Table"].get("GlobalSecondaryIndexes", [])
        gsi_names = [g["IndexName"] for g in gsis]
        assert "event_type-index" in gsi_names

    def test_dynamodb_table_has_device_id_gsi(self, dynamodb_client, sessions_config):
        """Verify DynamoDB table has device_id GSI."""
        response = dynamodb_client.describe_table(
            TableName=sessions_config["dynamodb_table_name"]
        )
        gsis = response["Table"].get("GlobalSecondaryIndexes", [])
        gsi_names = [g["IndexName"] for g in gsis]
        assert "device_id-index" in gsi_names


class TestS3Configuration:
    """Tests for S3 bucket configuration."""

    def test_s3_bucket_blocks_public_acls(self, s3_client, sessions_config):
        """Verify S3 bucket blocks public ACLs."""
        response = s3_client.get_public_access_block(
            Bucket=sessions_config["s3_bucket_name"]
        )
        assert response["PublicAccessBlockConfiguration"]["BlockPublicAcls"] is True

    def test_s3_bucket_blocks_public_policy(self, s3_client, sessions_config):
        """Verify S3 bucket blocks public policy."""
        response = s3_client.get_public_access_block(
            Bucket=sessions_config["s3_bucket_name"]
        )
        assert response["PublicAccessBlockConfiguration"]["BlockPublicPolicy"] is True

    def test_s3_bucket_ignores_public_acls(self, s3_client, sessions_config):
        """Verify S3 bucket ignores public ACLs."""
        response = s3_client.get_public_access_block(
            Bucket=sessions_config["s3_bucket_name"]
        )
        assert response["PublicAccessBlockConfiguration"]["IgnorePublicAcls"] is True

    def test_s3_bucket_restricts_public_buckets(self, s3_client, sessions_config):
        """Verify S3 bucket restricts public buckets."""
        response = s3_client.get_public_access_block(
            Bucket=sessions_config["s3_bucket_name"]
        )
        assert response["PublicAccessBlockConfiguration"]["RestrictPublicBuckets"] is True

    def test_s3_bucket_has_90_day_lifecycle_policy(self, s3_client, sessions_config):
        """Verify S3 bucket has 90-day expiration lifecycle rule."""
        response = s3_client.get_bucket_lifecycle_configuration(
            Bucket=sessions_config["s3_bucket_name"]
        )
        rules = response["Rules"]
        expiration_rule = next(
            (r for r in rules if r.get("Expiration", {}).get("Days") == 90),
            None
        )
        assert expiration_rule is not None


class TestCloudWatchLogsConfiguration:
    """Tests for CloudWatch Log Group configuration."""

    def test_handler_log_group_has_7_day_retention(self, logs_client, sessions_config):
        """Verify handler log group has 7-day retention."""
        response = logs_client.describe_log_groups(
            logGroupNamePrefix=sessions_config["handler_log_group"]
        )
        log_group = next(
            lg for lg in response["logGroups"]
            if lg["logGroupName"] == sessions_config["handler_log_group"]
        )
        assert log_group["retentionInDays"] == 7

    def test_export_log_group_has_7_day_retention(self, logs_client, sessions_config):
        """Verify export log group has 7-day retention."""
        response = logs_client.describe_log_groups(
            logGroupNamePrefix=sessions_config["export_log_group"]
        )
        log_group = next(
            lg for lg in response["logGroups"]
            if lg["logGroupName"] == sessions_config["export_log_group"]
        )
        assert log_group["retentionInDays"] == 7

    def test_crawler_trigger_log_group_has_7_day_retention(self, logs_client, sessions_config):
        """Verify crawler trigger log group has 7-day retention."""
        response = logs_client.describe_log_groups(
            logGroupNamePrefix=sessions_config["crawler_trigger_log_group"]
        )
        log_group = next(
            lg for lg in response["logGroups"]
            if lg["logGroupName"] == sessions_config["crawler_trigger_log_group"]
        )
        assert log_group["retentionInDays"] == 7


class TestBackupConfiguration:
    """Tests for AWS Backup configuration."""

    def test_backup_plan_has_30_day_retention(self, backup_client, sessions_config):
        """Verify backup plan has 30-day retention."""
        response = backup_client.list_backup_plans()
        plan = next(
            p for p in response["BackupPlansList"]
            if p["BackupPlanName"] == sessions_config["backup_plan_name"]
        )
        plan_details = backup_client.get_backup_plan(BackupPlanId=plan["BackupPlanId"])
        rules = plan_details["BackupPlan"]["Rules"]
        assert any(r["Lifecycle"]["DeleteAfterDays"] == 30 for r in rules)


class TestGlueConfiguration:
    """Tests for Glue configuration."""

    def test_glue_crawler_has_daily_schedule(self, glue_client, sessions_config):
        """Verify Glue crawler has daily schedule at 6 AM UTC."""
        response = glue_client.get_crawler(Name=sessions_config["glue_crawler_name"])
        schedule = response["Crawler"].get("Schedule", {}).get("ScheduleExpression", "")
        assert "cron(0 6" in schedule


class TestSchedulerConfiguration:
    """Tests for EventBridge Scheduler configuration."""

    def test_scheduler_has_daily_export_schedule(self, scheduler_client, sessions_config):
        """Verify scheduler runs daily export at 5 AM UTC."""
        response = scheduler_client.get_schedule(
            Name=sessions_config["scheduler_name"]
        )
        schedule = response["ScheduleExpression"]
        assert "cron(0 5" in schedule
