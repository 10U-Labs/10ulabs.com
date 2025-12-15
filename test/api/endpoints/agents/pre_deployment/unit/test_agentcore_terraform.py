"""Unit tests for agents AgentCore Terraform configuration."""
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


def test_agentcore_terraform_file_exists():
    """Verify agentcore.tf file exists."""
    agentcore_file = AGENTS_SRC / "agentcore.tf"
    assert agentcore_file.exists()


def test_agentcore_runtime_resource_exists():
    """Verify AgentCore runtime resource is defined."""
    agentcore_file = AGENTS_SRC / "agentcore.tf"
    with open(agentcore_file, encoding="utf-8") as f:
        content = f.read()
    # AgentCore resource should be defined
    has_agentcore = "agentcore" in content.lower() or "bedrock" in content.lower()
    assert has_agentcore
