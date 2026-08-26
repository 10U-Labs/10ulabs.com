class TestLambdaExistence:
    def test_sessions_handler_lambda_exists(self, lambda_client, sessions_config):
        response = lambda_client.get_function(
            FunctionName=sessions_config["handler_function_name"]
        )
        assert response["Configuration"]["FunctionName"] == sessions_config["handler_function_name"]

    def test_sessions_export_lambda_exists(self, lambda_client, sessions_config):
        response = lambda_client.get_function(
            FunctionName=sessions_config["export_function_name"]
        )
        assert response["Configuration"]["FunctionName"] == sessions_config["export_function_name"]

def test_dynamo_db_existence(dynamodb_client, sessions_config):
    response = dynamodb_client.describe_table(
        TableName=sessions_config["dynamodb_table_name"]
    )
    assert response["Table"]["TableName"] == sessions_config["dynamodb_table_name"]


def test_s3_existence(s3_client, sessions_config):
    response = s3_client.head_bucket(Bucket=sessions_config["s3_bucket_name"])
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


class TestCloudWatchLogsExistence:
    def test_handler_log_group_exists(self, logs_client, sessions_config):
        response = logs_client.describe_log_groups(
            logGroupNamePrefix=sessions_config["handler_log_group"]
        )
        log_groups = [lg["logGroupName"] for lg in response["logGroups"]]
        assert sessions_config["handler_log_group"] in log_groups

    def test_export_log_group_exists(self, logs_client, sessions_config):
        response = logs_client.describe_log_groups(
            logGroupNamePrefix=sessions_config["export_log_group"]
        )
        log_groups = [lg["logGroupName"] for lg in response["logGroups"]]
        assert sessions_config["export_log_group"] in log_groups

class TestBackupExistence:
    def test_backup_vault_exists(self, backup_client, sessions_config):
        response = backup_client.describe_backup_vault(
            BackupVaultName=sessions_config["backup_vault_name"]
        )
        assert response["BackupVaultName"] == sessions_config["backup_vault_name"]

    def test_backup_plan_exists(self, backup_client, sessions_config):
        response = backup_client.list_backup_plans()
        plan_names = [p["BackupPlanName"] for p in response["BackupPlansList"]]
        assert sessions_config["backup_plan_name"] in plan_names


def test_event_bridge_existence(scheduler_client, sessions_config):
    response = scheduler_client.get_schedule(
        Name=sessions_config["scheduler_name"]
    )
    assert response["Name"] == sessions_config["scheduler_name"]


class TestIamRoleExistence:
    def test_sessions_handler_iam_role_exists(self, iam_client, sessions_config):
        response = iam_client.get_role(RoleName=sessions_config["handler_role_name"])
        assert response["Role"]["RoleName"] == sessions_config["handler_role_name"]

    def test_sessions_export_iam_role_exists(self, iam_client, sessions_config):
        response = iam_client.get_role(RoleName=sessions_config["export_role_name"])
        assert response["Role"]["RoleName"] == sessions_config["export_role_name"]

    def test_scheduler_iam_role_exists(self, iam_client, sessions_config):
        response = iam_client.get_role(RoleName=sessions_config["scheduler_role_name"])
        assert response["Role"]["RoleName"] == sessions_config["scheduler_role_name"]

    def test_backup_iam_role_exists(self, iam_client, sessions_config):
        response = iam_client.get_role(RoleName=sessions_config["backup_role_name"])
        assert response["Role"]["RoleName"] == sessions_config["backup_role_name"]
