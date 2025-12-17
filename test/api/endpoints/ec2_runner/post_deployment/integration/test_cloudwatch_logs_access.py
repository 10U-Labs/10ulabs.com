"""Post-deployment integration tests for EC2 runner CloudWatch Logs access.

These tests verify that the deployed EC2 runner IAM role has CloudWatch Logs
permissions, enabling Docker containers running on EC2 runners to write logs
via the instance metadata service.
"""
import pytest
from botocore.exceptions import ClientError

from .conftest import get_inline_policy_actions


class TestEC2RunnerCloudWatchLogsPolicy:
    """Verify EC2 runner role has CloudWatch Logs permissions."""

    def test_01_ec2_runner_role_exists(self, iam_client, ec2_runner_role_name):
        """Verify the EC2 runner IAM role exists."""
        try:
            response = iam_client.get_role(RoleName=ec2_runner_role_name)
            assert response.get("Role") is not None
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(
                    f"EC2 runner role '{ec2_runner_role_name}' does not exist. "
                    "Run terraform apply in src/api/endpoints/ec2_runner/"
                )
            raise

    def test_02_ec2_runner_role_has_cloudwatch_logs_policy(
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

    def test_03_cloudwatch_logs_policy_allows_create_log_group(
        self, iam_client, ec2_runner_role_name
    ):
        """Verify CloudWatch Logs policy allows logs:CreateLogGroup action."""
        actions = get_inline_policy_actions(
            iam_client, ec2_runner_role_name, "CloudWatchLogsAccess"
        )
        assert "logs:CreateLogGroup" in actions

    def test_04_cloudwatch_logs_policy_allows_create_log_stream(
        self, iam_client, ec2_runner_role_name
    ):
        """Verify CloudWatch Logs policy allows logs:CreateLogStream action."""
        actions = get_inline_policy_actions(
            iam_client, ec2_runner_role_name, "CloudWatchLogsAccess"
        )
        assert "logs:CreateLogStream" in actions

    def test_05_cloudwatch_logs_policy_allows_put_log_events(
        self, iam_client, ec2_runner_role_name
    ):
        """Verify CloudWatch Logs policy allows logs:PutLogEvents action."""
        actions = get_inline_policy_actions(
            iam_client, ec2_runner_role_name, "CloudWatchLogsAccess"
        )
        assert "logs:PutLogEvents" in actions

    def test_06_cloudwatch_logs_policy_allows_describe_log_streams(
        self, iam_client, ec2_runner_role_name
    ):
        """Verify CloudWatch Logs policy allows logs:DescribeLogStreams action."""
        actions = get_inline_policy_actions(
            iam_client, ec2_runner_role_name, "CloudWatchLogsAccess"
        )
        assert "logs:DescribeLogStreams" in actions

    def test_07_cloudwatch_logs_policy_targets_github_runner_diag(
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
