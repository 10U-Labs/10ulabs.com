"""Layer 2: Configuration tests for rack designer endpoint.

Verify that resources created by this deployment are configured correctly.

Three-layer testing model:
- Layer 2: Configuration - Resources configured correctly
"""

from naming_conventions import validate_name, validate_kebab_name




class TestLambdaConfiguration:
    """Layer 2: Verify Lambda functions are configured correctly."""

    def test_handler_uses_python_runtime(self, lambda_client, handler_function_name):
        """Verify handler Lambda uses Python 3.13 runtime."""
        response = lambda_client.get_function(FunctionName=handler_function_name)
        runtime = response["Configuration"]["Runtime"]
        assert runtime == "python3.13", (
            f"Handler Lambda should use python3.13, got: {runtime}"
        )

    def test_handler_uses_arm64_architecture(
        self, lambda_client, handler_function_name
    ):
        """Verify handler Lambda uses ARM64 architecture."""
        response = lambda_client.get_function(FunctionName=handler_function_name)
        architectures = response["Configuration"].get("Architectures", ["x86_64"])
        assert "arm64" in architectures, (
            f"Handler Lambda should use arm64 architecture, got: {architectures}"
        )

    def test_handler_has_correct_timeout(self, lambda_client, handler_function_name):
        """Verify handler Lambda has correct timeout (10 seconds)."""
        response = lambda_client.get_function(FunctionName=handler_function_name)
        timeout = response["Configuration"]["Timeout"]
        assert timeout == 10, (
            f"Handler Lambda timeout should be 10 seconds, got: {timeout}"
        )


class TestCloudWatchLogsConfiguration:
    """Layer 2: Verify CloudWatch log groups are configured correctly."""

    def test_handler_log_group_has_retention_set(self, handler_log_group):
        """Verify handler log group has retention period configured."""
        assert handler_log_group["retention"] is not None, (
            f"Log group '{handler_log_group['name']}' should have retention set"
        )

    def test_handler_log_group_retention_is_7_days(self, handler_log_group):
        """Verify handler log group retention is 7 days per policy."""
        retention = handler_log_group["retention"]
        assert retention == 7, (
            f"Log group retention should be 7 days, got: {retention}"
        )


class TestDynamoDBConfiguration:
    """Layer 2: Verify DynamoDB tables are configured correctly."""

    def test_configurations_table_uses_pay_per_request(
        self, dynamodb_client, configurations_table_name
    ):
        """Verify configurations table uses PAY_PER_REQUEST billing mode."""
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
        """Verify configurations table has point-in-time recovery enabled."""
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
    """Layer 2: Verify resource names follow PascalCase conventions."""

    def test_handler_lambda_name_is_pascalcase(
        self, lambda_client, handler_function_name
    ):
        """Verify handler Lambda function name uses PascalCase."""
        response = lambda_client.get_function(FunctionName=handler_function_name)
        actual_name = response["Configuration"]["FunctionName"]
        error = validate_name(actual_name)
        assert error is None, (
            f"Handler Lambda has invalid name '{actual_name}': {error}"
        )

    def test_handler_role_name_is_pascalcase(self, iam_client, handler_role_name):
        """Verify handler IAM role name uses PascalCase."""
        response = iam_client.get_role(RoleName=handler_role_name)
        actual_name = response["Role"]["RoleName"]
        error = validate_name(actual_name)
        assert error is None, (
            f"Handler IAM role has invalid name '{actual_name}': {error}"
        )

    def test_backup_role_name_is_pascalcase(self, iam_client, backup_role_name):
        """Verify backup IAM role name uses PascalCase."""
        response = iam_client.get_role(RoleName=backup_role_name)
        actual_name = response["Role"]["RoleName"]
        error = validate_name(actual_name)
        assert error is None, (
            f"Backup IAM role has invalid name '{actual_name}': {error}"
        )

    def test_configurations_table_name_is_kebabcase(
        self, configurations_table_name
    ):
        """Verify configurations table name uses kebab-case."""
        error = validate_kebab_name(configurations_table_name)
        assert error is None, (
            f"Configurations table has invalid name '{configurations_table_name}': "
            f"{error}"
        )

    def test_backup_vault_name_is_kebabcase(self, backup_vault_name):
        """Verify backup vault name uses kebab-case."""
        error = validate_kebab_name(backup_vault_name)
        assert error is None, (
            f"Backup vault has invalid name '{backup_vault_name}': {error}"
        )


class TestBackupConfiguration:
    """Layer 2: Verify backup resources are configured correctly."""

    def test_backup_plan_exists(self, backup_plan_id, backup_plan_name):
        """Verify backup plan exists."""
        assert backup_plan_id is not None, (
            f"Backup plan '{backup_plan_name}' does not exist"
        )

    def test_backup_plan_has_daily_schedule(self, backup_client, backup_plan_id):
        """Verify backup plan has daily schedule at 5 AM UTC."""
        if backup_plan_id is None:
            assert False, "Backup plan not found"
        plan = backup_client.get_backup_plan(BackupPlanId=backup_plan_id)
        rules = plan["BackupPlan"]["Rules"]
        has_daily = any(
            r.get("ScheduleExpression") == "cron(0 5 * * ? *)" for r in rules
        )
        assert has_daily, (
            f"Backup plan should have daily schedule 'cron(0 5 * * ? *)', "
            f"got rules: {rules}"
        )

    def test_backup_plan_has_30_day_retention(self, backup_client, backup_plan_id):
        """Verify backup plan has 30-day retention."""
        if backup_plan_id is None:
            assert False, "Backup plan not found"
        plan = backup_client.get_backup_plan(BackupPlanId=backup_plan_id)
        rules = plan["BackupPlan"]["Rules"]
        has_30_day = any(
            r.get("Lifecycle", {}).get("DeleteAfterDays") == 30 for r in rules
        )
        assert has_30_day, (
            f"Backup plan should have 30-day retention, got rules: {rules}"
        )

    def test_backup_selection_includes_dynamodb_table(
        self, backup_client, backup_plan_id, configurations_table_arn
    ):
        """Verify backup selection includes the DynamoDB table."""
        if backup_plan_id is None:
            assert False, "Backup plan not found"
        selections = backup_client.list_backup_selections(BackupPlanId=backup_plan_id)
        for sel in selections.get("BackupSelectionsList", []):
            selection = backup_client.get_backup_selection(
                BackupPlanId=backup_plan_id,
                SelectionId=sel["SelectionId"]
            )
            resources = selection["BackupSelection"].get("Resources", [])
            if configurations_table_arn in resources:
                return
        assert False, (
            f"DynamoDB table '{configurations_table_arn}' not in backup selection"
        )
