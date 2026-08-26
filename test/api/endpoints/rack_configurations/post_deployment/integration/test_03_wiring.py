import pytest
from botocore.exceptions import ClientError


class TestLambdaWiring:
    def test_handler_has_api_gateway_permission(
        self, lambda_client, handler_function_name
    ):
        try:
            response = lambda_client.get_policy(FunctionName=handler_function_name)
            policy = response.get("Policy", "")
            assert "apigateway.amazonaws.com" in policy, (
                f"Lambda '{handler_function_name}' missing API Gateway invoke permission"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Lambda '{handler_function_name}' has no resource policy - "
                    "API Gateway cannot invoke it"
                )
            raise

    def test_handler_has_role_attached(self, lambda_client, handler_function_name):
        response = lambda_client.get_function(FunctionName=handler_function_name)
        role_arn = response["Configuration"].get("Role", "")
        assert role_arn, f"Lambda '{handler_function_name}' has no IAM role attached"

    def test_handler_role_follows_naming_pattern(
        self, lambda_client, handler_function_name, handler_role_name
    ):
        response = lambda_client.get_function(FunctionName=handler_function_name)
        role_arn = response["Configuration"].get("Role", "")
        assert handler_role_name in role_arn, (
            f"Lambda role ARN '{role_arn}' doesn't match expected pattern "
            f"containing '{handler_role_name}'"
        )


class TestHandlerIAMWiring:
    def test_handler_role_has_basic_execution_policy(
        self, iam_client, handler_role_name
    ):
        response = iam_client.list_attached_role_policies(RoleName=handler_role_name)
        policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
        basic_execution = (
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        assert basic_execution in policy_arns, (
            f"IAM role '{handler_role_name}' missing AWSLambdaBasicExecutionRole policy. "
            f"Attached policies: {policy_arns}"
        )

    def test_handler_role_has_dynamodb_policy(self, iam_client, handler_role_name):
        response = iam_client.list_role_policies(RoleName=handler_role_name)
        inline_policies = response.get("PolicyNames", [])
        has_dynamodb = any("DynamoDB" in p or "dynamodb" in p for p in inline_policies)
        assert has_dynamodb, (
            f"IAM role '{handler_role_name}' missing DynamoDB inline policy. "
            f"Available policies: {inline_policies}"
        )


class TestBackupIAMWiring:
    def test_backup_role_has_backup_policy(self, iam_client, backup_role_name):
        response = iam_client.list_attached_role_policies(RoleName=backup_role_name)
        policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
        expected = (
            "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
        )
        assert expected in policy_arns, (
            f"IAM role '{backup_role_name}' missing AWSBackupServiceRolePolicyForBackup. "
            f"Attached policies: {policy_arns}"
        )

    def test_backup_role_has_restore_policy(self, iam_client, backup_role_name):
        response = iam_client.list_attached_role_policies(RoleName=backup_role_name)
        policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
        expected = (
            "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
        )
        assert expected in policy_arns, (
            f"IAM role '{backup_role_name}' missing AWSBackupServiceRolePolicyForRestores. "
            f"Attached policies: {policy_arns}"
        )
