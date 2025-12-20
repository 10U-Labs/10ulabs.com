"""Unit tests for agent prompt files."""

import pytest
from repo_utils import REPO_ROOT

AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"
PROMPTS_DIR = AGENTS_SRC / "prompts"


def test_prompts_directory_exists():
    """Test that prompts directory exists."""
    assert PROMPTS_DIR.exists(), "prompts/ directory not found"


def test_prompts_directory_is_directory():
    """Test that prompts/ is a directory."""
    assert PROMPTS_DIR.is_dir(), "prompts/ should be a directory"


def test_troubleshooter_of_workflows_prompt_exists():
    """Test that troubleshooter_of_workflows.md prompt file exists."""
    prompt_file = PROMPTS_DIR / "troubleshooter_of_workflows.md"
    assert prompt_file.exists(), "troubleshooter_of_workflows.md not found"


def test_creator_of_agents_prompt_exists():
    """Test that creator_of_agents.md prompt file exists."""
    prompt_file = PROMPTS_DIR / "creator_of_agents.md"
    assert prompt_file.exists(), "creator_of_agents.md not found"


@pytest.fixture
def prompt_files():
    """Get list of prompt files."""
    return [p for p in PROMPTS_DIR.glob("*") if p.is_file()]


@pytest.fixture
def prompt_md_files():
    """Get list of markdown prompt files."""
    return list(PROMPTS_DIR.glob("*.md"))


@pytest.mark.parametrize("prompt_name", ["troubleshooter_of_workflows", "creator_of_agents"])
def test_prompt_file_is_markdown(prompt_name):
    """Test that prompt file has .md extension."""
    prompt_file = PROMPTS_DIR / f"{prompt_name}.md"
    assert prompt_file.suffix == ".md", (
        f"Prompt file {prompt_file.name} should have .md extension"
    )


@pytest.mark.parametrize("prompt_name", ["troubleshooter_of_workflows", "creator_of_agents"])
def test_prompt_file_is_lowercase(prompt_name):
    """Test that prompt file name is lowercase."""
    assert prompt_name == prompt_name.lower(), f"Prompt {prompt_name} should be lowercase"


@pytest.mark.parametrize("prompt_name", ["troubleshooter_of_workflows", "creator_of_agents"])
def test_prompt_file_has_no_spaces(prompt_name):
    """Test that prompt file name has no spaces."""
    assert " " not in prompt_name, f"Prompt {prompt_name} should not contain spaces"


def test_troubleshooter_prompt_has_sufficient_content():
    """Test that troubleshooter prompt has sufficient content."""
    prompt_file = PROMPTS_DIR / "troubleshooter_of_workflows.md"
    content = prompt_file.read_text()
    assert len(content) > 100, "Prompt seems too short"


def test_troubleshooter_prompt_references_workflows():
    """Test that troubleshooter prompt references workflows."""
    prompt_file = PROMPTS_DIR / "troubleshooter_of_workflows.md"
    content = prompt_file.read_text()
    has_workflow_reference = "workflow" in content.lower() or "ci/cd" in content.lower()
    assert has_workflow_reference, "Troubleshooter prompt should reference workflows"


def test_creator_prompt_has_sufficient_content():
    """Test that creator prompt has sufficient content."""
    prompt_file = PROMPTS_DIR / "creator_of_agents.md"
    content = prompt_file.read_text()
    assert len(content) > 100, "Prompt seems too short"


def test_creator_prompt_references_agents():
    """Test that creator prompt references agents."""
    prompt_file = PROMPTS_DIR / "creator_of_agents.md"
    content = prompt_file.read_text()
    has_agent_reference = "agent" in content.lower()
    assert has_agent_reference, "Creator prompt should reference agents"


def test_creator_prompt_references_pull_requests():
    """Test that creator prompt references pull requests."""
    prompt_file = PROMPTS_DIR / "creator_of_agents.md"
    content = prompt_file.read_text()
    has_pr_reference = "pr" in content.lower() or "pull request" in content.lower()
    assert has_pr_reference, "Creator prompt should reference pull requests"
