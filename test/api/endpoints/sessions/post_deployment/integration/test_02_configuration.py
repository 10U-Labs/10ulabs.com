from typing import Any, Dict
def _export_environment(lambda_client: Any, sessions_config: Dict[str, Any]) -> Dict[str, str]:
    response = lambda_client.get_function_configuration(
        FunctionName=sessions_config["export_function_name"]
    )
    return response.get("Environment", {}).get("Variables", {})


def _table_index_names(dynamodb_client: Any, sessions_config: Dict[str, Any]) -> list:
    response = dynamodb_client.describe_table(
        TableName=sessions_config["dynamodb_table_name"]
    )
    return [g["IndexName"] for g in response["Table"].get("GlobalSecondaryIndexes", [])]


class TestHandlerLambdaConfiguration:
    def test_handler_lambda_has_10_second_timeout(
        self,
        lambda_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["handler_function_name"]
        )
        assert response["Timeout"] == 10

    def test_handler_lambda_has_128mb_memory(
        self,
        lambda_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["handler_function_name"]
        )
        assert response["MemorySize"] == 128

    def test_handler_lambda_uses_arm64_architecture(
        self,
        lambda_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["handler_function_name"]
        )
        assert "arm64" in response["Architectures"]

    def test_handler_lambda_uses_python313_runtime(
        self,
        lambda_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["handler_function_name"]
        )
        assert response["Runtime"] == "python3.13"

    def test_handler_lambda_has_session_events_table_env_var(
        self,
        lambda_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["handler_function_name"]
        )
        env_vars = response.get("Environment", {}).get("Variables", {})
        assert "SESSION_EVENTS_TABLE" in env_vars


class TestExportLambdaConfiguration:
    def test_export_lambda_has_30_second_timeout(
        self,
        lambda_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        response = lambda_client.get_function_configuration(
            FunctionName=sessions_config["export_function_name"]
        )
        assert response["Timeout"] == 30

    def test_export_lambda_has_dynamodb_table_arn_env_var(
        self,
        lambda_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        env_vars = _export_environment(lambda_client, sessions_config)
        assert "DYNAMODB_TABLE_ARN" in env_vars

    def test_export_lambda_has_s3_bucket_env_var(
        self,
        lambda_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        env_vars = _export_environment(lambda_client, sessions_config)
        assert "S3_BUCKET" in env_vars

    def test_export_lambda_has_s3_prefix_env_var(
        self,
        lambda_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        env_vars = _export_environment(lambda_client, sessions_config)
        assert "S3_PREFIX" in env_vars


class TestDynamoDbConfiguration:
    def test_dynamodb_table_has_pay_per_request_billing(
        self,
        dynamodb_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        response = dynamodb_client.describe_table(
            TableName=sessions_config["dynamodb_table_name"]
        )
        assert response["Table"]["BillingModeSummary"]["BillingMode"] == "PAY_PER_REQUEST"

    def test_dynamodb_table_has_point_in_time_recovery(
        self,
        dynamodb_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        response = dynamodb_client.describe_continuous_backups(
            TableName=sessions_config["dynamodb_table_name"]
        )
        pitr = response["ContinuousBackupsDescription"]["PointInTimeRecoveryDescription"]
        assert pitr["PointInTimeRecoveryStatus"] == "ENABLED"

    def test_dynamodb_table_has_session_id_hash_key(
        self,
        dynamodb_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        response = dynamodb_client.describe_table(
            TableName=sessions_config["dynamodb_table_name"]
        )
        key_schema = response["Table"]["KeySchema"]
        hash_key = next(k for k in key_schema if k["KeyType"] == "HASH")
        assert hash_key["AttributeName"] == "session_id"

    def test_dynamodb_table_has_timestamp_range_key(
        self,
        dynamodb_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        response = dynamodb_client.describe_table(
            TableName=sessions_config["dynamodb_table_name"]
        )
        key_schema = response["Table"]["KeySchema"]
        range_key = next(k for k in key_schema if k["KeyType"] == "RANGE")
        assert range_key["AttributeName"] == "timestamp"

    def test_dynamodb_table_has_event_type_gsi(
        self,
        dynamodb_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        gsi_names = _table_index_names(dynamodb_client, sessions_config)
        assert "event_type-index" in gsi_names

    def test_dynamodb_table_has_device_id_gsi(
        self,
        dynamodb_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        gsi_names = _table_index_names(dynamodb_client, sessions_config)
        assert "device_id-index" in gsi_names


class TestS3Configuration:
    def test_s3_bucket_blocks_public_acls(
        self,
        s3_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        response = s3_client.get_public_access_block(
            Bucket=sessions_config["s3_bucket_name"]
        )
        assert response["PublicAccessBlockConfiguration"]["BlockPublicAcls"] is True

    def test_s3_bucket_blocks_public_policy(
        self,
        s3_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        response = s3_client.get_public_access_block(
            Bucket=sessions_config["s3_bucket_name"]
        )
        assert response["PublicAccessBlockConfiguration"]["BlockPublicPolicy"] is True

    def test_s3_bucket_ignores_public_acls(
        self,
        s3_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        response = s3_client.get_public_access_block(
            Bucket=sessions_config["s3_bucket_name"]
        )
        assert response["PublicAccessBlockConfiguration"]["IgnorePublicAcls"] is True

    def test_s3_bucket_restricts_public_buckets(
        self,
        s3_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        response = s3_client.get_public_access_block(
            Bucket=sessions_config["s3_bucket_name"]
        )
        assert response["PublicAccessBlockConfiguration"]["RestrictPublicBuckets"] is True

    def test_s3_bucket_has_90_day_lifecycle_policy(
        self,
        s3_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
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
    def test_handler_log_group_has_7_day_retention(
        self,
        logs_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        response = logs_client.describe_log_groups(
            logGroupNamePrefix=sessions_config["handler_log_group"]
        )
        log_group = next(
            lg for lg in response["logGroups"]
            if lg["logGroupName"] == sessions_config["handler_log_group"]
        )
        assert log_group["retentionInDays"] == 7

    def test_export_log_group_has_7_day_retention(
        self,
        logs_client: Any,
        sessions_config: Dict[str, Any]
    ) -> None:
        response = logs_client.describe_log_groups(
            logGroupNamePrefix=sessions_config["export_log_group"]
        )
        log_group = next(
            lg for lg in response["logGroups"]
            if lg["logGroupName"] == sessions_config["export_log_group"]
        )
        assert log_group["retentionInDays"] == 7

def test_backup_configuration(backup_client: Any, sessions_config: Dict[str, Any]) -> None:
    response = backup_client.list_backup_plans()
    plan = next(
        p for p in response["BackupPlansList"]
        if p["BackupPlanName"] == sessions_config["backup_plan_name"]
    )
    plan_details = backup_client.get_backup_plan(BackupPlanId=plan["BackupPlanId"])
    rules = plan_details["BackupPlan"]["Rules"]
    assert any(r["Lifecycle"]["DeleteAfterDays"] == 30 for r in rules)


def test_scheduler_configuration(scheduler_client: Any, sessions_config: Dict[str, Any]) -> None:
    response = scheduler_client.get_schedule(
        Name=sessions_config["scheduler_name"]
    )
    schedule = response["ScheduleExpression"]
    assert "cron(0 5" in schedule
