"""Layer 2: Configuration tests.

Verify resources created by this deployment are configured correctly.
"""
import pytest
from botocore.exceptions import ClientError

from naming_conventions import validate_name

from .conftest import get_inline_policy_actions

pytestmark = pytest.mark.layer(2)


def test_lambda_function_name_is_pascalcase(lambda_client, lambda_function_name):
    """Verify Lambda function name uses PascalCase."""
    response = lambda_client.get_function(FunctionName=lambda_function_name)
    actual_name = response['Configuration']['FunctionName']
    error = validate_name(actual_name)
    assert error is None, (
        f"Deployed Lambda function has invalid name '{actual_name}': {error}"
    )


class TestIAMRoleNaming:
    """Verify IAM role naming conventions."""

    def test_lambda_role_name_is_pascalcase(self, iam_client, lambda_role_name):
        """Verify Lambda IAM role name uses PascalCase."""
        response = iam_client.get_role(RoleName=lambda_role_name)
        actual_name = response['Role']['RoleName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed IAM role has invalid name '{actual_name}': {error}"
        )

    def test_ec2_runner_role_name_is_pascalcase(
        self, iam_client, ec2_runner_role_name
    ):
        """Verify EC2 runner IAM role name uses PascalCase."""
        response = iam_client.get_role(RoleName=ec2_runner_role_name)
        actual_name = response['Role']['RoleName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed IAM role has invalid name '{actual_name}': {error}"
        )


class TestLambdaRoleKmsPolicy:
    """Verify Lambda role has KMS permissions."""

    def test_lambda_role_has_kms_policy(self, iam_client, lambda_role_name):
        """Verify the Lambda role has a KMS policy attached."""
        try:
            response = iam_client.list_role_policies(RoleName=lambda_role_name)
            policy_names = response.get("PolicyNames", [])
            assert "KMSDecrypt" in policy_names, (
                f"Lambda role '{lambda_role_name}' missing KMSDecrypt inline policy. "
                f"Found policies: {policy_names}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip(f"Lambda role '{lambda_role_name}' does not exist")
            raise

    def test_kms_policy_allows_decrypt(self, iam_client, lambda_role_name):
        """Verify the KMS policy allows kms:Decrypt action."""
        try:
            response = iam_client.get_role_policy(
                RoleName=lambda_role_name,
                PolicyName="KMSDecrypt"
            )
            policy_doc = response.get("PolicyDocument", {})
            statements = policy_doc.get("Statement", [])
            allows_decrypt = False
            for statement in statements:
                actions = statement.get("Action", [])
                if isinstance(actions, str):
                    actions = [actions]
                if "kms:Decrypt" in actions and statement.get("Effect") == "Allow":
                    allows_decrypt = True
                    break
            assert allows_decrypt, (
                f"KMSDecrypt policy on '{lambda_role_name}' does not allow kms:Decrypt"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip(f"KMSDecrypt policy not found on role '{lambda_role_name}'")
            raise


class TestHandlerLogGroupConfiguration:
    """Verify Lambda handler CloudWatch log group is configured correctly."""

    def test_handler_log_group_has_retention_set(self, handler_log_group):
        """Verify log group has retention policy configured."""
        assert handler_log_group["retention"] is not None, (
            f"Log group '{handler_log_group['name']}' has no retention policy set"
        )

    def test_handler_log_group_retention_is_7_days(self, handler_log_group):
        """Verify log group retention is set to 7 days."""
        retention = handler_log_group["retention"]
        assert retention == 7, (
            f"Log group '{handler_log_group['name']}' retention is {retention} days, "
            "expected 7 days"
        )


class TestEC2RunnerCloudWatchLogsPolicy:
    """Verify EC2 runner role has CloudWatch Logs permissions."""

    def test_ec2_runner_role_has_cloudwatch_logs_policy(
        self, iam_client, ec2_runner_role_name
    ):
        """Verify the EC2 runner role has CloudWatch Logs policy attached."""
        try:
            response = iam_client.list_role_policies(RoleName=ec2_runner_role_name)
            policy_names = response.get("PolicyNames", [])
            assert "CloudWatchLogsAccess" in policy_names, (
                f"EC2 runner role '{ec2_runner_role_name}' missing CloudWatchLogsAccess "
                f"inline policy. Found policies: {policy_names}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip(f"EC2 runner role '{ec2_runner_role_name}' does not exist")
            raise

    def test_cloudwatch_logs_policy_allows_create_log_group(
        self, iam_client, ec2_runner_role_name
    ):
        """Verify CloudWatch Logs policy allows logs:CreateLogGroup action."""
        actions = get_inline_policy_actions(
            iam_client, ec2_runner_role_name, "CloudWatchLogsAccess"
        )
        assert "logs:CreateLogGroup" in actions

    def test_cloudwatch_logs_policy_allows_create_log_stream(
        self, iam_client, ec2_runner_role_name
    ):
        """Verify CloudWatch Logs policy allows logs:CreateLogStream action."""
        actions = get_inline_policy_actions(
            iam_client, ec2_runner_role_name, "CloudWatchLogsAccess"
        )
        assert "logs:CreateLogStream" in actions

    def test_cloudwatch_logs_policy_allows_put_log_events(
        self, iam_client, ec2_runner_role_name
    ):
        """Verify CloudWatch Logs policy allows logs:PutLogEvents action."""
        actions = get_inline_policy_actions(
            iam_client, ec2_runner_role_name, "CloudWatchLogsAccess"
        )
        assert "logs:PutLogEvents" in actions

    def test_cloudwatch_logs_policy_allows_describe_log_streams(
        self, iam_client, ec2_runner_role_name
    ):
        """Verify CloudWatch Logs policy allows logs:DescribeLogStreams action."""
        actions = get_inline_policy_actions(
            iam_client, ec2_runner_role_name, "CloudWatchLogsAccess"
        )
        assert "logs:DescribeLogStreams" in actions

    def test_cloudwatch_logs_policy_targets_github_runner_diag(
        self, iam_client, ec2_runner_role_name
    ):
        """Verify CloudWatch Logs policy targets /github-runner/diag log group."""
        try:
            response = iam_client.get_role_policy(
                RoleName=ec2_runner_role_name,
                PolicyName="CloudWatchLogsAccess"
            )
            statements = response.get("PolicyDocument", {}).get("Statement", [])
            found = any(
                "/github-runner/diag" in str(stmt.get("Resource", []))
                for stmt in statements
            )
            assert found, (
                f"CloudWatchLogsAccess policy on '{ec2_runner_role_name}' does not "
                f"target /github-runner/diag log group"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip(
                    f"CloudWatchLogsAccess policy not found on '{ec2_runner_role_name}'"
                )
            raise
