from naming_conventions import validate_name, validate_kebab_name


class TestLambdaConfiguration:
    def test_handler_uses_python_runtime(self, lambda_client, handler_function_name):
        response = lambda_client.get_function(FunctionName=handler_function_name)
        runtime = response["Configuration"]["Runtime"]
        assert runtime == "python3.13", (
            f"Handler Lambda should use python3.13, got: {runtime}"
        )

    def test_handler_uses_arm64_architecture(
        self, lambda_client, handler_function_name
    ):
        response = lambda_client.get_function(FunctionName=handler_function_name)
        architectures = response["Configuration"].get("Architectures", ["x86_64"])
        assert "arm64" in architectures, (
            f"Handler Lambda should use arm64 architecture, got: {architectures}"
        )

    def test_handler_has_correct_timeout(self, lambda_client, handler_function_name):
        response = lambda_client.get_function(FunctionName=handler_function_name)
        timeout = response["Configuration"]["Timeout"]
        assert timeout == 10, (
            f"Handler Lambda timeout should be 10 seconds, got: {timeout}"
        )


class TestCloudWatchLogsConfiguration:
    def test_handler_log_group_has_retention_set(self, handler_log_group):
        assert handler_log_group["retention"] is not None, (
            f"Log group '{handler_log_group['name']}' should have retention set"
        )

    def test_handler_log_group_retention_is_7_days(self, handler_log_group):
        retention = handler_log_group["retention"]
        assert retention == 7, (
            f"Log group retention should be 7 days, got: {retention}"
        )


class TestDynamoDBConfiguration:
    def test_configurations_table_uses_pay_per_request(
        self, dynamodb_client, configurations_table_name
    ):
        response = dynamodb_client.describe_table(TableName=configurations_table_name)
        billing_mode = response["Table"].get("BillingModeSummary", {}).get(
            "BillingMode", "PROVISIONED"
        )
        assert billing_mode == "PAY_PER_REQUEST", (
            f"Configurations table should use PAY_PER_REQUEST, got: {billing_mode}"
        )

    def test_configurations_table_has_pitr_enabled(
        self, dynamodb_client, configurations_table_name
    ):
        response = dynamodb_client.describe_continuous_backups(
            TableName=configurations_table_name
        )
        pitr_status = response["ContinuousBackupsDescription"][
            "PointInTimeRecoveryDescription"
        ]["PointInTimeRecoveryStatus"]
        assert pitr_status == "ENABLED", (
            f"Configurations table should have PITR enabled, got: {pitr_status}"
        )


class TestNamingConventions:
    def test_handler_lambda_name_is_pascalcase(
        self, lambda_client, handler_function_name
    ):
        response = lambda_client.get_function(FunctionName=handler_function_name)
        actual_name = response["Configuration"]["FunctionName"]
        error = validate_name(actual_name)
        assert error is None, (
            f"Handler Lambda has invalid name '{actual_name}': {error}"
        )

    def test_handler_role_name_is_pascalcase(self, iam_client, handler_role_name):
        response = iam_client.get_role(RoleName=handler_role_name)
        actual_name = response["Role"]["RoleName"]
        error = validate_name(actual_name)
        assert error is None, (
            f"Handler IAM role has invalid name '{actual_name}': {error}"
        )

    def test_backup_role_name_is_pascalcase(self, iam_client, backup_role_name):
        response = iam_client.get_role(RoleName=backup_role_name)
        actual_name = response["Role"]["RoleName"]
        error = validate_name(actual_name)
        assert error is None, (
            f"Backup IAM role has invalid name '{actual_name}': {error}"
        )

    def test_configurations_table_name_is_kebabcase(
        self, configurations_table_name
    ):
        error = validate_kebab_name(configurations_table_name)
        assert error is None, (
            f"Configurations table has invalid name '{configurations_table_name}': "
            f"{error}"
        )

    def test_backup_vault_name_is_kebabcase(self, backup_vault_name):
        error = validate_kebab_name(backup_vault_name)
        assert error is None, (
            f"Backup vault has invalid name '{backup_vault_name}': {error}"
        )


class TestBackupConfiguration:
    def test_backup_plan_exists(self, backup_plan_id, backup_plan_name):
        assert backup_plan_id is not None, (
            f"Backup plan '{backup_plan_name}' does not exist"
        )

    def test_backup_plan_has_daily_schedule(self, backup_client, backup_plan_id):
        plan = backup_client.get_backup_plan(BackupPlanId=backup_plan_id)
        rules = plan["BackupPlan"]["Rules"]
        schedules = [r.get("ScheduleExpression") for r in rules]
        assert "cron(0 5 * * ? *)" in schedules

    def test_backup_plan_has_30_day_retention(self, backup_client, backup_plan_id):
        plan = backup_client.get_backup_plan(BackupPlanId=backup_plan_id)
        rules = plan["BackupPlan"]["Rules"]
        retentions = [r.get("Lifecycle", {}).get("DeleteAfterDays") for r in rules]
        assert 30 in retentions

    def test_backup_selection_includes_dynamodb_table(
        self, backup_client, backup_plan_id, configurations_table_arn
    ):
        selections = backup_client.list_backup_selections(BackupPlanId=backup_plan_id)
        all_resources = []
        for sel in selections.get("BackupSelectionsList", []):
            selection = backup_client.get_backup_selection(
                BackupPlanId=backup_plan_id,
                SelectionId=sel["SelectionId"]
            )
            all_resources.extend(selection["BackupSelection"].get("Resources", []))
        assert configurations_table_arn in all_resources
