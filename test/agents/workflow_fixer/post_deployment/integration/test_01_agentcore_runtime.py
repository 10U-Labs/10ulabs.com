"""Integration tests for Workflow Fixer AgentCore Runtime.

Five-layer testing model:
- Layer 2: Authorization - Can we call AgentCore APIs?
- Layer 3: Existence - Does the runtime exist?
- Layer 4: Configuration - Is it configured correctly?
"""

from botocore.exceptions import ClientError
import pytest


class TestAgentCoreAuthorization:
    """Layer 2: Verify we can call AgentCore APIs."""

    def test_01_can_call_list_agent_runtimes_api(self, agentcore_client):
        """Verify we have permission to list agent runtimes."""
        try:
            agentcore_client.list_agent_runtimes(maxResults=1)
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call ListAgentRuntimes. "
                    "Check IAM permissions for bedrock-agentcore:ListAgentRuntimes."
                )
            raise

    def test_02_list_runtimes_returns_valid_response(self, agentcore_client):
        """Verify ListAgentRuntimes returns expected structure."""
        response = agentcore_client.list_agent_runtimes(maxResults=10)
        assert "agentRuntimeSummaries" in response, (
            "ListAgentRuntimes response missing 'agentRuntimeSummaries' key"
        )


class TestAgentCoreRuntimeExistence:
    """Layer 3: Verify the AgentCore Runtime exists."""

    def test_01_runtime_exists(self, agentcore_client, agent_runtime_name):
        """Verify the Workflow Fixer agent runtime exists."""
        try:
            response = agentcore_client.list_agent_runtimes(maxResults=100)
            runtimes = response.get("agentRuntimeSummaries", [])
            runtime_names = [r["agentRuntimeName"] for r in runtimes]
            assert agent_runtime_name in runtime_names, (
                f"Agent runtime '{agent_runtime_name}' not found. "
                f"Available runtimes: {runtime_names}. "
                "Run terraform apply in src/agents/workflow_fixer/"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Agent runtime '{agent_runtime_name}' does not exist. "
                    "Run terraform apply in src/agents/workflow_fixer/"
                )
            raise

    def test_02_runtime_has_active_status(self, agentcore_client, agent_runtime_name):
        """Verify the agent runtime has ACTIVE status."""
        response = agentcore_client.list_agent_runtimes(maxResults=100)
        runtimes = response.get("agentRuntimeSummaries", [])
        runtime = next(
            (r for r in runtimes if r["agentRuntimeName"] == agent_runtime_name), None
        )
        if not runtime:
            pytest.skip(f"Agent runtime '{agent_runtime_name}' not found")
        status = runtime.get("status")
        assert status == "ACTIVE", (
            f"Agent runtime status is '{status}', expected 'ACTIVE'"
        )


class TestECRRepositoryExistence:
    """Layer 3: Verify the ECR repository exists."""

    def test_01_ecr_repository_exists(self, ecr_client, ecr_repo_name):
        """Verify the ECR repository for the agent container exists."""
        try:
            response = ecr_client.describe_repositories(
                repositoryNames=[ecr_repo_name]
            )
            repos = response.get("repositories", [])
            assert len(repos) == 1, f"ECR repository '{ecr_repo_name}' not found"
        except ClientError as err:
            if err.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.fail(
                    f"ECR repository '{ecr_repo_name}' does not exist. "
                    "Run terraform apply in src/agents/workflow_fixer/"
                )
            raise

    def test_02_ecr_repository_has_images(self, ecr_client, ecr_repo_name):
        """Verify the ECR repository has at least one image."""
        try:
            response = ecr_client.list_images(
                repositoryName=ecr_repo_name, maxResults=1
            )
            images = response.get("imageIds", [])
            if not images:
                pytest.skip("No images in ECR repository yet (first deployment)")
        except ClientError as err:
            if err.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("ECR repository does not exist")
            raise


class TestWebhookLambdaExistence:
    """Layer 3: Verify the webhook Lambda exists."""

    def test_01_lambda_function_exists(self, lambda_client, lambda_function_name):
        """Verify the webhook Lambda function exists."""
        try:
            response = lambda_client.get_function(FunctionName=lambda_function_name)
            assert response["Configuration"]["FunctionName"] == lambda_function_name
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Lambda function '{lambda_function_name}' does not exist. "
                    "Run terraform apply in src/agents/workflow_fixer/"
                )
            raise

    def test_02_lambda_has_function_url(self, lambda_client, lambda_function_name):
        """Verify the Lambda has a function URL configured."""
        try:
            response = lambda_client.get_function_url_config(
                FunctionName=lambda_function_name
            )
            assert "FunctionUrl" in response, "Lambda missing function URL"
            assert response["FunctionUrl"].startswith("https://"), (
                "Function URL should be HTTPS"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Lambda function URL not configured for '{lambda_function_name}'"
                )
            raise


class TestWebhookLambdaConfiguration:
    """Layer 4: Verify the webhook Lambda is configured correctly."""

    def test_01_lambda_has_correct_runtime(self, lambda_client, lambda_function_name):
        """Verify the Lambda uses Python 3.13 runtime."""
        response = lambda_client.get_function(FunctionName=lambda_function_name)
        runtime = response["Configuration"]["Runtime"]
        assert runtime == "python3.13", (
            f"Lambda runtime is '{runtime}', expected 'python3.13'"
        )

    def test_02_lambda_has_agent_runtime_arn_env_var(
        self, lambda_client, lambda_function_name
    ):
        """Verify the Lambda has AGENT_RUNTIME_ARN environment variable."""
        response = lambda_client.get_function(FunctionName=lambda_function_name)
        env_vars = response["Configuration"].get("Environment", {}).get(
            "Variables", {}
        )
        assert "AGENT_RUNTIME_ARN" in env_vars, (
            "Lambda missing AGENT_RUNTIME_ARN environment variable"
        )
        assert env_vars["AGENT_RUNTIME_ARN"].startswith(
            "arn:aws:bedrock-agentcore:"
        ), "AGENT_RUNTIME_ARN should be a valid AgentCore ARN"

    def test_03_lambda_has_ssm_github_pat_env_var(
        self, lambda_client, lambda_function_name
    ):
        """Verify the Lambda has SSM_GITHUB_PAT environment variable."""
        response = lambda_client.get_function(FunctionName=lambda_function_name)
        env_vars = response["Configuration"].get("Environment", {}).get(
            "Variables", {}
        )
        assert "SSM_GITHUB_PAT" in env_vars, (
            "Lambda missing SSM_GITHUB_PAT environment variable"
        )
