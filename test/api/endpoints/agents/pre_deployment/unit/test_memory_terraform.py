"""Unit tests for agents AgentCore Memory Terraform configuration."""
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


def test_memory_terraform_file_exists():
    """Verify memory.tf file exists."""
    memory_file = AGENTS_SRC / "memory.tf"
    assert memory_file.exists()


def test_memory_resource_exists():
    """Verify AgentCore Memory resource is defined."""
    memory_file = AGENTS_SRC / "memory.tf"
    with open(memory_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_bedrockagentcore_memory"' in content


def test_memory_has_session_configuration():
    """Verify memory has session memory configuration."""
    memory_file = AGENTS_SRC / "memory.tf"
    with open(memory_file, encoding="utf-8") as f:
        content = f.read()
    assert "session_memory_configuration" in content


def test_memory_has_semantic_configuration():
    """Verify memory has semantic memory configuration."""
    memory_file = AGENTS_SRC / "memory.tf"
    with open(memory_file, encoding="utf-8") as f:
        content = f.read()
    assert "semantic_memory_configuration" in content


def test_memory_uses_opensearch_serverless():
    """Verify memory uses OpenSearch Serverless for vector storage."""
    memory_file = AGENTS_SRC / "memory.tf"
    with open(memory_file, encoding="utf-8") as f:
        content = f.read()
    assert "opensearch_serverless" in content.lower()


def test_opensearch_collection_resource_exists():
    """Verify OpenSearch Serverless collection resource is defined."""
    memory_file = AGENTS_SRC / "memory.tf"
    with open(memory_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_opensearchserverless_collection"' in content


def test_opensearch_security_policy_resource_exists():
    """Verify OpenSearch Serverless security policy resource is defined."""
    memory_file = AGENTS_SRC / "memory.tf"
    with open(memory_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_opensearchserverless_security_policy"' in content


def test_opensearch_encryption_policy_exists():
    """Verify OpenSearch Serverless encryption policy is defined."""
    memory_file = AGENTS_SRC / "memory.tf"
    with open(memory_file, encoding="utf-8") as f:
        content = f.read()
    assert 'type = "encryption"' in content


def test_opensearch_network_policy_exists():
    """Verify OpenSearch Serverless network policy is defined."""
    memory_file = AGENTS_SRC / "memory.tf"
    with open(memory_file, encoding="utf-8") as f:
        content = f.read()
    assert 'type = "network"' in content


def test_opensearch_access_policy_exists():
    """Verify OpenSearch Serverless access policy is defined."""
    memory_file = AGENTS_SRC / "memory.tf"
    with open(memory_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_opensearchserverless_access_policy"' in content
