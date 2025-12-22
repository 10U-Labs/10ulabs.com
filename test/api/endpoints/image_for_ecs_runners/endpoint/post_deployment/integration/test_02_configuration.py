"""Layer 2: Configuration tests.

Verify resources created by this deployment are configured correctly.
"""
from botocore.exceptions import ClientError
import pytest

from naming_conventions import validate_name

pytestmark = pytest.mark.layer(2)


@pytest.fixture(name="lambda_function", scope="module")
def lambda_function_fixture(lambda_client):
    """Find and return the Lambda function matching ImageForEcsRunners."""
    response = lambda_client.list_functions()
    matching = [
        f for f in response["Functions"]
        if "ImageForEcsRunners" in f["FunctionName"]
    ]
    if not matching:
        pytest.skip("Lambda function not found")
    return matching[0]


@pytest.fixture(name="lambda_config", scope="module")
def lambda_config_fixture(lambda_client, lambda_function):
    """Get the Lambda function configuration."""
    return lambda_client.get_function_configuration(
        FunctionName=lambda_function["FunctionName"]
    )


@pytest.fixture(name="env_vars", scope="module")
def env_vars_fixture(lambda_config):
    """Get environment variables from Lambda config."""
    return lambda_config.get("Environment", {}).get("Variables", {})


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
