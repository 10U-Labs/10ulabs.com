"""Unit tests for agents AgentCore Terraform configuration."""
from repo_utils import REPO_ROOT

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
    assert 'resource "aws_bedrockagentcore_agent_runtime"' in content


def test_agentcore_has_code_configuration():
    """Verify AgentCore has code configuration."""
    agentcore_file = AGENTS_SRC / "agentcore.tf"
    with open(agentcore_file, encoding="utf-8") as f:
        content = f.read()
    assert "code_configuration" in content


def test_agentcore_no_container_configuration():
    """Verify AgentCore does not use container configuration."""
    agentcore_file = AGENTS_SRC / "agentcore.tf"
    with open(agentcore_file, encoding="utf-8") as f:
        content = f.read()
    assert "container_configuration" not in content


def test_agentcore_uses_python_runtime():
    """Verify AgentCore uses Python runtime."""
    agentcore_file = AGENTS_SRC / "agentcore.tf"
    with open(agentcore_file, encoding="utf-8") as f:
        content = f.read()
    assert "python" in content.lower()


def test_agentcore_has_guardrail_configuration():
    """Verify AgentCore has guardrail configuration."""
    agentcore_file = AGENTS_SRC / "agentcore.tf"
    with open(agentcore_file, encoding="utf-8") as f:
        content = f.read()
    assert "guardrail_configuration" in content


def test_agentcore_has_environment_variables():
    """Verify AgentCore has environment_variables block."""
    agentcore_file = AGENTS_SRC / "agentcore.tf"
    with open(agentcore_file, encoding="utf-8") as f:
        content = f.read()
    assert "environment_variables" in content


def test_agentcore_has_prompts_bucket_env_var():
    """Verify AgentCore has PROMPTS_BUCKET environment variable."""
    agentcore_file = AGENTS_SRC / "agentcore.tf"
    with open(agentcore_file, encoding="utf-8") as f:
        content = f.read()
    assert "PROMPTS_BUCKET" in content


def test_agentcore_has_guardrail_id_env_var():
    """Verify AgentCore has GUARDRAIL_ID environment variable."""
    agentcore_file = AGENTS_SRC / "agentcore.tf"
    with open(agentcore_file, encoding="utf-8") as f:
        content = f.read()
    assert "GUARDRAIL_ID" in content


def test_agentcore_has_memory_arn_env_var():
    """Verify AgentCore has MEMORY_ARN environment variable."""
    agentcore_file = AGENTS_SRC / "agentcore.tf"
    with open(agentcore_file, encoding="utf-8") as f:
        content = f.read()
    assert "MEMORY_ARN" in content


def test_agentcore_has_archive_data_source():
    """Verify AgentCore uses archive data source for code packaging."""
    agentcore_file = AGENTS_SRC / "agentcore.tf"
    with open(agentcore_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file"' in content


def test_agentcore_has_runtime_code_bucket():
    """Verify S3 bucket for runtime code exists."""
    agentcore_file = AGENTS_SRC / "agentcore.tf"
    with open(agentcore_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_bucket" "runtime_code"' in content


def test_agentcore_uploads_runtime_code_to_s3():
    """Verify runtime code is uploaded to S3."""
    agentcore_file = AGENTS_SRC / "agentcore.tf"
    with open(agentcore_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_object" "runtime_code"' in content
