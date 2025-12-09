"""Integration tests for Agent Creator."""

from botocore.exceptions import ClientError
import pytest


class TestAgentCoreRuntimeExistence:
    """Verify the AgentCore Runtime exists."""

    def test_01_runtime_exists(self, agentcore_client, agent_runtime_name):
        """Verify the Agent Creator runtime exists."""
        try:
            response = agentcore_client.list_agent_runtimes(maxResults=100)
            runtimes = response.get("agentRuntimeSummaries", [])
            runtime_names = [r["agentRuntimeName"] for r in runtimes]
            assert agent_runtime_name in runtime_names, (
                f"Agent runtime '{agent_runtime_name}' not found. "
                f"Available runtimes: {runtime_names}."
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(f"Agent runtime '{agent_runtime_name}' does not exist.")
            raise


class TestECRRepositoryExistence:
    """Verify the ECR repository exists."""

    def test_01_ecr_repository_exists(self, ecr_client, ecr_repo_name):
        """Verify the ECR repository exists."""
        try:
            response = ecr_client.describe_repositories(
                repositoryNames=[ecr_repo_name]
            )
            repos = response.get("repositories", [])
            assert len(repos) == 1, f"ECR repository '{ecr_repo_name}' not found"
        except ClientError as err:
            if err.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.fail(f"ECR repository '{ecr_repo_name}' does not exist.")
            raise


class TestLambdaExistence:
    """Verify the Lambda exists."""

    def test_01_lambda_function_exists(self, lambda_client, lambda_function_name):
        """Verify the Lambda function exists."""
        try:
            response = lambda_client.get_function(FunctionName=lambda_function_name)
            assert response["Configuration"]["FunctionName"] == lambda_function_name
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(f"Lambda function '{lambda_function_name}' does not exist.")
            raise

    def test_02_lambda_has_function_url(self, lambda_client, lambda_function_name):
        """Verify the Lambda has a function URL."""
        try:
            response = lambda_client.get_function_url_config(
                FunctionName=lambda_function_name
            )
            assert "FunctionUrl" in response
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(f"Lambda function URL not configured.")
            raise
