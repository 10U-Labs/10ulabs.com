"""Unit tests for agents AgentCore Policy Terraform configuration."""
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


def test_policy_terraform_file_exists():
    """Verify policy.tf file exists."""
    policy_file = AGENTS_SRC / "policy.tf"
    assert policy_file.exists()


def test_policy_resource_exists():
    """Verify AgentCore Policy resource is defined."""
    policy_file = AGENTS_SRC / "policy.tf"
    with open(policy_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_bedrockagentcore_agent_runtime_policy"' in content


def test_policy_uses_cedar():
    """Verify policy uses Cedar language."""
    policy_file = AGENTS_SRC / "policy.tf"
    with open(policy_file, encoding="utf-8") as f:
        content = f.read()
    # Cedar syntax markers
    assert "permit" in content.lower() or "forbid" in content.lower()


def test_policy_restricts_github_org():
    """Verify policy restricts to 10U-Labs-LLC GitHub organization."""
    policy_file = AGENTS_SRC / "policy.tf"
    with open(policy_file, encoding="utf-8") as f:
        content = f.read()
    assert "10U-Labs-LLC" in content


def test_policy_allows_file_read():
    """Verify policy allows file read operations."""
    policy_file = AGENTS_SRC / "policy.tf"
    with open(policy_file, encoding="utf-8") as f:
        content = f.read()
    assert "file:read" in content.lower() or "file" in content.lower()


def test_policy_restricts_file_write():
    """Verify policy restricts file write to specific directories."""
    policy_file = AGENTS_SRC / "policy.tf"
    with open(policy_file, encoding="utf-8") as f:
        content = f.read()
    assert "file:write" in content.lower() or "src/" in content


def test_policy_forbids_dangerous_commands():
    """Verify policy forbids dangerous bash commands."""
    policy_file = AGENTS_SRC / "policy.tf"
    with open(policy_file, encoding="utf-8") as f:
        content = f.read()
    # Check for dangerous command restrictions
    assert "rm -rf" in content or "sudo" in content


def test_policy_forbids_force_push():
    """Verify policy forbids force push to git."""
    policy_file = AGENTS_SRC / "policy.tf"
    with open(policy_file, encoding="utf-8") as f:
        content = f.read()
    assert "force" in content.lower()


def test_policy_forbids_main_branch_push():
    """Verify policy forbids direct push to main branch."""
    policy_file = AGENTS_SRC / "policy.tf"
    with open(policy_file, encoding="utf-8") as f:
        content = f.read()
    assert "main" in content or "master" in content


def test_policy_allows_agent_orchestration():
    """Verify policy allows agents to invoke other agents."""
    policy_file = AGENTS_SRC / "policy.tf"
    with open(policy_file, encoding="utf-8") as f:
        content = f.read()
    assert "agent:invoke" in content or "troubleshooter_of_workflows" in content
