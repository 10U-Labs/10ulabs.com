"""Tests to validate the Lambda function after deployment.

These tests verify that the Lambda function is deployed correctly
and can be invoked.
"""
import json

from botocore.exceptions import ClientError
import pytest


class TestLambdaFunctionExistence:
    """Verify the Lambda function exists and is configured."""

    def test_01_lambda_function_exists(self, lambda_client):
        """Verify the Lambda function exists."""
        try:
            # Look for a function with our expected name pattern
            response = lambda_client.list_functions()
            function_names = [f["FunctionName"] for f in response["Functions"]]

            matching_functions = [
                name for name in function_names
                if "ImageForEcsRunners" in name
            ]

            assert len(matching_functions) > 0, (
                "No Lambda function found matching 'ImageForEcsRunners'. "
                "Run terraform apply in src/api/endpoints/image_for_ecs_runners/"
            )
        except ClientError as e:
            pytest.fail(f"Failed to list Lambda functions: {e}")

    def test_02_lambda_function_configured(self, lambda_client):
        """Verify the Lambda function has correct configuration."""
        try:
            response = lambda_client.list_functions()
            matching_functions = [
                f for f in response["Functions"]
                if "ImageForEcsRunners" in f["FunctionName"]
            ]

            if not matching_functions:
                pytest.skip("Lambda function not found")

            function = matching_functions[0]

            # Verify runtime
            assert function["Runtime"].startswith("python"), (
                f"Expected Python runtime, got {function['Runtime']}"
            )

            # Verify handler
            assert function["Handler"] == "handler.lambda_handler", (
                f"Expected handler 'handler.lambda_handler', got {function['Handler']}"
            )
        except ClientError as e:
            pytest.fail(f"Failed to get Lambda function: {e}")


class TestLambdaFunctionEnvironment:
    """Verify the Lambda function environment variables."""

    def test_01_has_ecr_repository_env(self, lambda_client):
        """Verify ECR_REPOSITORY environment variable is set."""
        try:
            response = lambda_client.list_functions()
            matching_functions = [
                f for f in response["Functions"]
                if "ImageForEcsRunners" in f["FunctionName"]
            ]

            if not matching_functions:
                pytest.skip("Lambda function not found")

            function_name = matching_functions[0]["FunctionName"]
            config = lambda_client.get_function_configuration(
                FunctionName=function_name
            )

            env_vars = config.get("Environment", {}).get("Variables", {})
            assert "ECR_REPOSITORY" in env_vars, (
                "ECR_REPOSITORY environment variable not set"
            )
            assert env_vars["ECR_REPOSITORY"], (
                "ECR_REPOSITORY environment variable is empty"
            )
        except ClientError as e:
            pytest.fail(f"Failed to get Lambda function configuration: {e}")

    def test_02_has_github_repo_env(self, lambda_client):
        """Verify GITHUB_REPO environment variable is set."""
        try:
            response = lambda_client.list_functions()
            matching_functions = [
                f for f in response["Functions"]
                if "ImageForEcsRunners" in f["FunctionName"]
            ]

            if not matching_functions:
                pytest.skip("Lambda function not found")

            function_name = matching_functions[0]["FunctionName"]
            config = lambda_client.get_function_configuration(
                FunctionName=function_name
            )

            env_vars = config.get("Environment", {}).get("Variables", {})
            assert "GITHUB_REPO" in env_vars, (
                "GITHUB_REPO environment variable not set"
            )
            assert env_vars["GITHUB_REPO"], (
                "GITHUB_REPO environment variable is empty"
            )
        except ClientError as e:
            pytest.fail(f"Failed to get Lambda function configuration: {e}")

    def test_03_has_github_token_secret_name_env(self, lambda_client):
        """Verify GITHUB_TOKEN_SECRET_NAME environment variable is set."""
        try:
            response = lambda_client.list_functions()
            matching_functions = [
                f for f in response["Functions"]
                if "ImageForEcsRunners" in f["FunctionName"]
            ]

            if not matching_functions:
                pytest.skip("Lambda function not found")

            function_name = matching_functions[0]["FunctionName"]
            config = lambda_client.get_function_configuration(
                FunctionName=function_name
            )

            env_vars = config.get("Environment", {}).get("Variables", {})
            assert "GITHUB_TOKEN_SECRET_NAME" in env_vars, (
                "GITHUB_TOKEN_SECRET_NAME environment variable not set"
            )
            assert env_vars["GITHUB_TOKEN_SECRET_NAME"], (
                "GITHUB_TOKEN_SECRET_NAME environment variable is empty"
            )
        except ClientError as e:
            pytest.fail(f"Failed to get Lambda function configuration: {e}")


class TestLambdaFunctionInvocation:
    """Verify the Lambda function can be invoked directly."""

    def test_01_can_invoke_with_options(self, lambda_client):
        """Verify the Lambda function handles OPTIONS requests."""
        try:
            response = lambda_client.list_functions()
            matching_functions = [
                f for f in response["Functions"]
                if "ImageForEcsRunners" in f["FunctionName"]
            ]

            if not matching_functions:
                pytest.skip("Lambda function not found")

            function_name = matching_functions[0]["FunctionName"]

            # Invoke with OPTIONS request
            event = {
                "httpMethod": "OPTIONS",
                "path": "/v1/image-for-ecs-runners",
                "headers": {}
            }

            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(event)
            )

            # Parse response
            payload = json.loads(response["Payload"].read())

            assert payload["statusCode"] == 200, (
                f"Expected 200 status, got {payload['statusCode']}"
            )
            assert "Access-Control-Allow-Origin" in payload["headers"], (
                "Missing CORS headers in response"
            )
        except ClientError as e:
            pytest.fail(f"Failed to invoke Lambda function: {e}")

    def test_02_returns_cors_headers_for_options(self, lambda_client):
        """Verify the Lambda function returns proper CORS headers."""
        try:
            response = lambda_client.list_functions()
            matching_functions = [
                f for f in response["Functions"]
                if "ImageForEcsRunners" in f["FunctionName"]
            ]

            if not matching_functions:
                pytest.skip("Lambda function not found")

            function_name = matching_functions[0]["FunctionName"]

            event = {
                "httpMethod": "OPTIONS",
                "path": "/v1/image-for-ecs-runners",
                "headers": {}
            }

            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(event)
            )

            payload = json.loads(response["Payload"].read())
            headers = payload.get("headers", {})

            assert headers.get("Access-Control-Allow-Origin") == "*", (
                "Expected '*' for Access-Control-Allow-Origin"
            )
            assert "GET" in headers.get("Access-Control-Allow-Methods", ""), (
                "Expected 'GET' in Access-Control-Allow-Methods"
            )
        except ClientError as e:
            pytest.fail(f"Failed to invoke Lambda function: {e}")
