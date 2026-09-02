from typing import Any, Optional
class TestLambdaConfiguration:
    def test_handler_uses_python_runtime(
        self,
        lambda_client: Any,
        handler_function_name: str
    ) -> None:
        response = lambda_client.get_function(FunctionName=handler_function_name)
        runtime = response["Configuration"]["Runtime"]
        assert runtime == "python3.13", (
            f"Handler Lambda should use python3.13, got: {runtime}"
        )

    def test_handler_uses_arm64_architecture(
        self, lambda_client: Any, handler_function_name: str
    ) -> None:
        response = lambda_client.get_function(FunctionName=handler_function_name)
        architectures = response["Configuration"].get("Architectures", ["x86_64"])
        assert "arm64" in architectures, (
            f"Handler Lambda should use arm64 architecture, got: {architectures}"
        )

    def test_handler_has_correct_timeout(
        self,
        lambda_client: Any,
        handler_function_name: str
    ) -> None:
        response = lambda_client.get_function(FunctionName=handler_function_name)
        timeout = response["Configuration"]["Timeout"]
        assert timeout == 10, (
            f"Handler Lambda timeout should be 10 seconds, got: {timeout}"
        )


class TestCloudWatchLogsConfiguration:
    def test_handler_log_group_has_retention_set(self, handler_log_group: Any) -> None:
        assert handler_log_group["retention"] is not None, (
            f"Log group '{handler_log_group['name']}' should have retention set"
        )

    def test_handler_log_group_retention_is_7_days(self, handler_log_group: Any) -> None:
        retention = handler_log_group["retention"]
        assert retention == 7, (
            f"Log group retention should be 7 days, got: {retention}"
        )


class TestDynamoDBConfiguration:
    def test_configurations_table_uses_pay_per_request(
        self, dynamodb_client: Any, configurations_table_name: str
    ) -> None:
        response = dynamodb_client.describe_table(TableName=configurations_table_name)
        billing_mode = response["Table"].get("BillingModeSummary", {}).get(
            "BillingMode", "PROVISIONED"
        )
        assert billing_mode == "PAY_PER_REQUEST", (
            f"Configurations table should use PAY_PER_REQUEST, got: {billing_mode}"
        )

    def test_configurations_table_has_pitr_enabled(
        self, dynamodb_client: Any, configurations_table_name: str
    ) -> None:
        response = dynamodb_client.describe_continuous_backups(
            TableName=configurations_table_name
        )
        pitr_status = response["ContinuousBackupsDescription"][
            "PointInTimeRecoveryDescription"
        ]["PointInTimeRecoveryStatus"]
        assert pitr_status == "ENABLED", (
            f"Configurations table should have PITR enabled, got: {pitr_status}"
        )


class TestBackupConfiguration:
    def test_backup_plan_exists(self, backup_plan_id: Optional[str], backup_plan_name: str) -> None:
        assert backup_plan_id is not None, (
            f"Backup plan '{backup_plan_name}' does not exist"
        )

    def test_backup_plan_has_daily_schedule(
        self,
        backup_client: Any,
        backup_plan_id: Optional[str]
    ) -> None:
        plan = backup_client.get_backup_plan(BackupPlanId=backup_plan_id)
        rules = plan["BackupPlan"]["Rules"]
        schedules = [r.get("ScheduleExpression") for r in rules]
        assert "cron(0 5 * * ? *)" in schedules

    def test_backup_plan_has_30_day_retention(
        self,
        backup_client: Any,
        backup_plan_id: Optional[str]
    ) -> None:
        plan = backup_client.get_backup_plan(BackupPlanId=backup_plan_id)
        rules = plan["BackupPlan"]["Rules"]
        retentions = [r.get("Lifecycle", {}).get("DeleteAfterDays") for r in rules]
        assert 30 in retentions

    def test_backup_selection_includes_dynamodb_table(
        self, backup_client: Any, backup_plan_id: Optional[str], configurations_table_arn: str
    ) -> None:
        selections = backup_client.list_backup_selections(BackupPlanId=backup_plan_id)
        all_resources = []
        for sel in selections.get("BackupSelectionsList", []):
            selection = backup_client.get_backup_selection(
                BackupPlanId=backup_plan_id,
                SelectionId=sel["SelectionId"]
            )
            all_resources.extend(selection["BackupSelection"].get("Resources", []))
        assert configurations_table_arn in all_resources
