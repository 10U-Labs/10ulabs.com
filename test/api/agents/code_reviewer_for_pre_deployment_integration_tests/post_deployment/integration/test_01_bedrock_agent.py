"""Integration tests for Test Auditor AgentCore Runtime.

Five-layer testing model:
- Layer 2: Authorization - Can we call AgentCore APIs?
- Layer 3: Existence - Does the runtime/gateway exist?
- Layer 4: Configuration - Is it configured correctly?
"""

from botocore.exceptions import ClientError
import pytest


class TestAgentCoreAuthorization:
    """Layer 2: Verify we can call AgentCore APIs."""

    def test_01_can_call_list_agent_runtimes_api(self, bedrock_agent_client):
        """Verify we have permission to list agent runtimes."""
        try:
            bedrock_agent_client.list_agent_runtimes(maxResults=1)
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call ListAgentRuntimes. "
                    "Check IAM permissions for bedrock:ListAgentRuntimes."
                )
            raise

    def test_02_list_runtimes_returns_valid_response(self, bedrock_agent_client):
        """Verify ListAgentRuntimes returns expected structure."""
        response = bedrock_agent_client.list_agent_runtimes(maxResults=10)
        assert "agentRuntimeSummaries" in response, (
            "ListAgentRuntimes response missing 'agentRuntimeSummaries' key"
        )


class TestAgentCoreExistence:
    """Layer 3: Verify the AgentCore Runtime exists."""

    def test_01_runtime_exists(self, bedrock_agent_client, agent_name):
        """Verify the Test Auditor agent runtime exists."""
        try:
            response = bedrock_agent_client.list_agent_runtimes(maxResults=100)
            runtimes = response.get("agentRuntimeSummaries", [])
            runtime_names = [r["agentRuntimeName"] for r in runtimes]
            assert agent_name in runtime_names, (
                f"Agent runtime '{agent_name}' not found. "
                f"Available runtimes: {runtime_names}. "
                "Run terraform apply in src/api/agents/test_auditor/"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Agent runtime '{agent_name}' does not exist. "
                    "Run terraform apply in src/api/agents/test_auditor/"
                )
            raise

    def test_02_runtime_has_status(self, bedrock_agent_client, agent_name):
        """Verify the agent runtime has a valid status."""
        response = bedrock_agent_client.list_agent_runtimes(maxResults=100)
        runtimes = response.get("agentRuntimeSummaries", [])
        runtime = next(
            (r for r in runtimes if r["agentRuntimeName"] == agent_name), None
        )
        if not runtime:
            pytest.skip(f"Agent runtime '{agent_name}' not found")
        assert "status" in runtime, "Agent runtime missing status field"


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
                    "Run terraform apply in src/api/agents/test_auditor/"
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
