"""Post-deployment integration tests for agents/shared ECR configuration."""
import json


def test_agents_ecr_repository_exists(ecr_client):
    """Test that the agents ECR repository exists."""
    response = ecr_client.describe_repositories(repositoryNames=["10ulabs-agents"])
    assert len(response["repositories"]) == 1


def test_agents_ecr_repository_has_scan_on_push_enabled(ecr_client):
    """Test that scan on push is enabled for the agents repository."""
    response = ecr_client.describe_repositories(repositoryNames=["10ulabs-agents"])
    repo = response["repositories"][0]
    assert repo["imageScanningConfiguration"]["scanOnPush"] is True


def test_agents_ecr_repository_policy_exists(ecr_client):
    """Test that a repository policy exists for the agents ECR repository."""
    response = ecr_client.get_repository_policy(repositoryName="10ulabs-agents")
    assert "policyText" in response


def test_agents_ecr_repository_policy_allows_bedrock_agentcore(ecr_client):
    """Test that the repository policy allows Bedrock AgentCore service principal."""
    response = ecr_client.get_repository_policy(repositoryName="10ulabs-agents")
    policy = json.loads(response["policyText"])

    agentcore_allowed = False
    for statement in policy.get("Statement", []):
        principal = statement.get("Principal", {})
        service = principal.get("Service", "")
        if isinstance(service, list):
            if "agentcore.bedrock.amazonaws.com" in service:
                agentcore_allowed = True
                break
        elif service == "agentcore.bedrock.amazonaws.com":
            agentcore_allowed = True
            break

    assert agentcore_allowed, (
        "ECR repository policy must allow agentcore.bedrock.amazonaws.com "
        "service principal for Bedrock AgentCore to validate ECR URIs"
    )
