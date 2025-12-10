"""Tests to validate the Lambda function after deployment.

These tests verify that the Lambda function is deployed correctly
and can be invoked.
"""
import json

import pytest


@pytest.fixture(name="lambda_function", scope="module")
def lambda_function_fixture(lambda_client):
    """Find and return the Lambda function matching ImageForEcsRunners."""
    response = lambda_client.list_functions()
    matching = [
        f for f in response["Functions"]
        if "ImageForEcsRunners" in f["FunctionName"]
    ]
    if not matching:
        pytest.fail(
            "No Lambda function found matching 'ImageForEcsRunners'. "
            "Run terraform apply in src/api/endpoints/image_for_ecs_runners/"
        )
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


@pytest.fixture(name="options_response", scope="module")
def options_response_fixture(lambda_client, lambda_function):
    """Invoke Lambda with OPTIONS request and return response."""
    event = {
        "httpMethod": "OPTIONS",
        "path": "/v1/image-for-ecs-runners",
        "headers": {}
    }
    response = lambda_client.invoke(
        FunctionName=lambda_function["FunctionName"],
        InvocationType="RequestResponse",
        Payload=json.dumps(event)
    )
    return json.loads(response["Payload"].read())


class TestLambdaFunctionExistence:
    """Verify the Lambda function exists and is configured."""

    def test_01_lambda_function_exists(self, lambda_function):
        """Verify the Lambda function exists."""
        assert lambda_function is not None

    def test_02_lambda_uses_python_runtime(self, lambda_function):
        """Verify the Lambda function uses Python runtime."""
        assert lambda_function["Runtime"].startswith("python")

    def test_03_lambda_has_correct_handler(self, lambda_function):
        """Verify the Lambda function has correct handler."""
        assert lambda_function["Handler"] == "handler.lambda_handler"


class TestLambdaFunctionEnvironment:
    """Verify the Lambda function environment variables."""

    def test_01_ecr_repository_env_exists(self, env_vars):
        """Verify ECR_REPOSITORY environment variable exists."""
        assert "ECR_REPOSITORY" in env_vars

    def test_02_ecr_repository_env_not_empty(self, env_vars):
        """Verify ECR_REPOSITORY environment variable is not empty."""
        assert env_vars.get("ECR_REPOSITORY")

    def test_03_github_repo_env_exists(self, env_vars):
        """Verify GITHUB_REPO environment variable exists."""
        assert "GITHUB_REPO" in env_vars

    def test_04_github_repo_env_not_empty(self, env_vars):
        """Verify GITHUB_REPO environment variable is not empty."""
        assert env_vars.get("GITHUB_REPO")

    def test_05_github_token_secret_name_env_exists(self, env_vars):
        """Verify GITHUB_TOKEN_SECRET_NAME environment variable exists."""
        assert "GITHUB_TOKEN_SECRET_NAME" in env_vars

    def test_06_github_token_secret_name_env_not_empty(self, env_vars):
        """Verify GITHUB_TOKEN_SECRET_NAME environment variable is not empty."""
        assert env_vars.get("GITHUB_TOKEN_SECRET_NAME")


class TestLambdaFunctionInvocation:
    """Verify the Lambda function can be invoked directly."""

    def test_01_options_returns_200(self, options_response):
        """Verify OPTIONS request returns 200 status."""
        assert options_response["statusCode"] == 200

    def test_02_options_has_cors_origin_header(self, options_response):
        """Verify OPTIONS response has Access-Control-Allow-Origin header."""
        assert "Access-Control-Allow-Origin" in options_response["headers"]

    def test_03_cors_origin_is_wildcard(self, options_response):
        """Verify Access-Control-Allow-Origin is '*'."""
        assert options_response["headers"]["Access-Control-Allow-Origin"] == "*"

    def test_04_cors_methods_includes_get(self, options_response):
        """Verify Access-Control-Allow-Methods includes GET."""
        methods = options_response["headers"].get("Access-Control-Allow-Methods", "")

        assert "GET" in methods
