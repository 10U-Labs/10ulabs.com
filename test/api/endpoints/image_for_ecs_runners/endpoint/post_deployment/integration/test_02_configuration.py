"""Layer 2: Configuration tests.

Verify resources created by this deployment are configured correctly.
"""
from botocore.exceptions import ClientError
import pytest

from naming_conventions import validate_name

pytestmark = pytest.mark.layer(2)


class TestLambdaRuntime:
    """Verify Lambda function runtime configuration."""

    def test_lambda_uses_python_runtime(self, lambda_function):
        """Verify the Lambda function uses Python runtime."""
        assert lambda_function["Runtime"].startswith("python")

    def test_lambda_has_correct_handler(self, lambda_function):
        """Verify the Lambda function has correct handler."""
        assert lambda_function["Handler"] == "handler.lambda_handler"


class TestLambdaEnvironmentVariables:
    """Verify Lambda function environment variables."""

    def test_ecr_repository_env_exists(self, env_vars):
        """Verify ECR_REPOSITORY environment variable exists."""
        assert "ECR_REPOSITORY" in env_vars

    def test_ecr_repository_env_not_empty(self, env_vars):
        """Verify ECR_REPOSITORY environment variable is not empty."""
        assert env_vars.get("ECR_REPOSITORY")

    def test_github_repo_env_exists(self, env_vars):
        """Verify GITHUB_REPO environment variable exists."""
        assert "GITHUB_REPO" in env_vars

    def test_github_repo_env_not_empty(self, env_vars):
        """Verify GITHUB_REPO environment variable is not empty."""
        assert env_vars.get("GITHUB_REPO")

    def test_github_token_secret_name_env_exists(self, env_vars):
        """Verify GITHUB_TOKEN_SECRET_NAME environment variable exists."""
        assert "GITHUB_TOKEN_SECRET_NAME" in env_vars

    def test_github_token_secret_name_env_not_empty(self, env_vars):
        """Verify GITHUB_TOKEN_SECRET_NAME environment variable is not empty."""
        assert env_vars.get("GITHUB_TOKEN_SECRET_NAME")


class TestNamingConventions:
    """Verify deployed resources follow naming conventions."""

    def test_lambda_function_name_is_pascalcase(self, lambda_function):
        """Verify Lambda function name uses PascalCase."""
        actual_name = lambda_function["FunctionName"]
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed Lambda function has invalid name '{actual_name}': {error}"
        )

    def test_lambda_role_name_is_pascalcase(self, iam_client, lambda_function):
        """Verify Lambda IAM role name uses PascalCase."""
        role_name = f"{lambda_function['FunctionName']}ServiceRole"
        try:
            response = iam_client.get_role(RoleName=role_name)
            actual_name = response['Role']['RoleName']
            error = validate_name(actual_name)
            assert error is None, (
                f"Deployed IAM role has invalid name '{actual_name}': {error}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip(f"IAM role '{role_name}' does not exist")
            raise


class TestCloudWatchLogGroupConfiguration:
    """Verify CloudWatch log group is configured correctly."""

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
