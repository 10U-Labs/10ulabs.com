"""Integration tests for Test Auditor Lambda Action Group.

Five-layer testing model:
- Layer 2: Authorization - Can we call Lambda APIs?
- Layer 3: Existence - Does the Lambda function exist?
- Layer 4: Configuration - Is it configured correctly?
- Layer 5: Capability - Can we invoke it?
"""

import json

from botocore.exceptions import ClientError
import pytest


class TestLambdaAuthorization:
    """Layer 2: Verify we can call Lambda APIs."""

    def test_01_can_call_get_function_api(self, lambda_client, lambda_function_name):
        """Verify we have permission to call lambda:GetFunction."""
        try:
            lambda_client.get_function(FunctionName=lambda_function_name)
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "AccessDeniedException":
                pytest.fail(
                    f"No permission to call GetFunction on '{lambda_function_name}'. "
                    "Check IAM permissions for lambda:GetFunction."
                )
            if code == "ResourceNotFoundException":
                pass  # Existence check is in next layer
            else:
                raise

    def test_02_can_call_list_functions_api(self, lambda_client):
        """Verify we have permission to call lambda:ListFunctions."""
        try:
            lambda_client.list_functions(MaxItems=1)
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call ListFunctions. "
                    "Check IAM permissions for lambda:ListFunctions."
                )
            raise


class TestLambdaExistence:
    """Layer 3: Verify the Lambda function exists."""

    def test_01_function_exists(self, lambda_client, lambda_function_name):
        """Verify the action group Lambda function exists."""
        try:
            response = lambda_client.get_function(FunctionName=lambda_function_name)
            assert response["Configuration"]["FunctionName"] == lambda_function_name
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Lambda function '{lambda_function_name}' does not exist. "
                    "Run terraform apply in src/api/agents/test_auditor/"
                )
            raise

    def test_02_function_has_arn(self, lambda_client, lambda_function_name):
        """Verify the Lambda function has a valid ARN."""
        try:
            response = lambda_client.get_function(FunctionName=lambda_function_name)
            arn = response["Configuration"].get("FunctionArn", "")
            assert arn.startswith("arn:aws:lambda:"), f"Invalid ARN: {arn}"
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip("Lambda function does not exist")
            raise


class TestLambdaConfiguration:
    """Layer 4: Verify the Lambda function is configured correctly."""

    def test_01_has_required_environment_variables(
        self, lambda_client, lambda_function_name
    ):
        """Verify the Lambda has required environment variables."""
        try:
            response = lambda_client.get_function(FunctionName=lambda_function_name)
            env_vars = response["Configuration"].get("Environment", {}).get(
                "Variables", {}
            )
            required_vars = ["GITHUB_ORG", "GITHUB_REPO", "SSM_GITHUB_PAT"]
            missing = [v for v in required_vars if v not in env_vars]
            assert not missing, (
                f"Lambda missing required environment variables: {missing}. "
                f"Found: {list(env_vars.keys())}"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip("Lambda function does not exist")
            raise

    def test_02_has_correct_runtime(self, lambda_client, lambda_function_name):
        """Verify the Lambda uses Python 3.13 runtime."""
        try:
            response = lambda_client.get_function(FunctionName=lambda_function_name)
            runtime = response["Configuration"]["Runtime"]
            assert runtime == "python3.13", (
                f"Lambda runtime is '{runtime}', expected 'python3.13'"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip("Lambda function does not exist")
            raise


class TestLambdaCapability:
    """Layer 5: Verify we can invoke the Lambda function."""

    def test_01_can_invoke_list_test_directories(
        self, lambda_client, lambda_function_name
    ):
        """Verify we can invoke the list_test_directories function."""
        try:
            payload = {
                "actionGroup": "GitHubOperations",
                "function": "list_test_directories",
                "parameters": []
            }
            response = lambda_client.invoke(
                FunctionName=lambda_function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(payload)
            )
            result = json.loads(response["Payload"].read())
            assert "response" in result, (
                f"Unexpected response format: {result}"
            )
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "AccessDeniedException":
                pytest.fail(
                    f"No permission to invoke '{lambda_function_name}'. "
                    "Check IAM permissions for lambda:InvokeFunction."
                )
            if code == "ResourceNotFoundException":
                pytest.skip("Lambda function does not exist")
            raise

    def test_02_can_invoke_get_documented_approach(
        self, lambda_client, lambda_function_name
    ):
        """Verify we can invoke the get_documented_approach function."""
        try:
            payload = {
                "actionGroup": "GitHubOperations",
                "function": "get_documented_approach",
                "parameters": []
            }
            response = lambda_client.invoke(
                FunctionName=lambda_function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(payload)
            )
            result = json.loads(response["Payload"].read())
            assert "response" in result, f"Unexpected response format: {result}"
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip("Lambda function does not exist")
            raise
