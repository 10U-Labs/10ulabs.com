import pytest
from botocore.exceptions import ClientError


class TestHandlerLambdaWiring:
    def test_handler_lambda_can_be_invoked_by_api_gateway(self, lambda_client, sessions_config):
        try:
            response = lambda_client.get_policy(
                FunctionName=sessions_config["handler_function_name"]
            )
            policy = response["Policy"]
            assert "apigateway.amazonaws.com" in policy
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail("Lambda policy not found - API Gateway permission missing")
            raise

    def test_handler_lambda_role_has_dynamodb_policy(self, iam_client, sessions_config):
        response = iam_client.list_role_policies(
            RoleName=sessions_config["handler_role_name"]
        )
        policy_names = response["PolicyNames"]
        assert "DynamoDBAccess" in policy_names

    def test_handler_lambda_role_has_basic_execution_policy(self, iam_client, sessions_config):
        response = iam_client.list_attached_role_policies(
            RoleName=sessions_config["handler_role_name"]
        )
        policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
        assert any("AWSLambdaBasicExecutionRole" in arn for arn in policy_arns)


class TestExportLambdaWiring:
    def test_export_lambda_role_has_export_permissions(self, iam_client, sessions_config):
        response = iam_client.list_role_policies(
            RoleName=sessions_config["export_role_name"]
        )
        policy_names = response["PolicyNames"]
        assert "ExportPermissions" in policy_names

    def test_export_lambda_role_has_s3_write_permission(self, iam_client, sessions_config):
        response = iam_client.get_role_policy(
            RoleName=sessions_config["export_role_name"],
            PolicyName="ExportPermissions"
        )
        policy_doc = response["PolicyDocument"]
        statements = policy_doc.get("Statement", [])
        s3_actions = []
        for stmt in statements:
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]
            s3_actions.extend([a for a in actions if a.startswith("s3:")])
        assert "s3:PutObject" in s3_actions


def test_scheduler_wiring(iam_client, sessions_config):
    response = iam_client.list_role_policies(
        RoleName=sessions_config["scheduler_role_name"]
    )
    policy_names = response["PolicyNames"]
    assert "InvokeLambda" in policy_names


def test_backup_wiring(backup_client, sessions_config):
    plans_response = backup_client.list_backup_plans()
    plan = next(
        p for p in plans_response["BackupPlansList"]
        if p["BackupPlanName"] == sessions_config["backup_plan_name"]
    )
    plan_id = plan["BackupPlanId"]

    selections_response = backup_client.list_backup_selections(
        BackupPlanId=plan_id
    )
    assert len(selections_response["BackupSelectionsList"]) > 0
