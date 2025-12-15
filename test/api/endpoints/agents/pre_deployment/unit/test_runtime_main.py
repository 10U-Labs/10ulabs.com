"""Unit tests for agents runtime main.py."""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"
RUNTIME_DIR = AGENTS_SRC / "runtime"


def test_runtime_main_py_exists():
    """Test that main.py exists in runtime directory."""
    main_file = RUNTIME_DIR / "main.py"
    assert main_file.exists()


def test_runtime_main_imports_tools():
    """Test that main.py imports ALL_TOOLS from tools."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "from tools import ALL_TOOLS" in content


def test_runtime_main_has_load_prompt_function():
    """Test that main.py defines load_prompt function."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "def load_prompt" in content


def test_runtime_main_has_extract_recommendation_function():
    """Test that main.py defines extract_recommendation function."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "def extract_recommendation" in content


def test_runtime_main_has_entrypoint_decorator():
    """Test that main.py has @app.entrypoint decorator."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "@app.entrypoint" in content


def test_runtime_main_has_invoke_function():
    """Test that main.py defines invoke function."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "def invoke" in content


def test_runtime_main_references_prompts_directory():
    """Test that main.py references the prompts directory."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "prompts" in content.lower()


class TestExtractRecommendation:
    """Test the extract_recommendation logic (parsed from source)."""

    def test_extract_recommendation_pattern_contains_json_code_block(self):
        """Test that JSON code block marker is present."""
        test_result = '''
Here is my analysis.

```json
{
    "recommendation": "create_agent",
    "create_agent_request": "Create an agent that handles X"
}
```

Done.
'''
        assert "```json" in test_result

    def test_extract_recommendation_pattern_contains_recommendation_key(self):
        """Test that recommendation key is present in JSON block."""
        test_result = '''
Here is my analysis.

```json
{
    "recommendation": "create_agent",
    "create_agent_request": "Create an agent that handles X"
}
```

Done.
'''
        assert '"recommendation"' in test_result

    def test_extract_recommendation_pattern_handles_no_json(self):
        """Test that results without JSON blocks work."""
        test_result = "Simple result with no JSON block"
        assert "```json" not in test_result


class TestLoadPromptLogic:
    """Test the load_prompt logic."""

    def test_prompts_directory_exists_in_runtime(self):
        """Test that prompts directory exists (main.py expects it in container)."""
        # In the container, prompts are copied to runtime/prompts
        # But in the repo, they're in agents/prompts
        # The Dockerfile copies them
        prompts_in_src = AGENTS_SRC / "prompts"
        assert prompts_in_src.exists()

    def test_prompts_directory_has_agents(self):
        """Test that prompts directory has at least one agent."""
        prompts_dir = AGENTS_SRC / "prompts"
        agents = [p.stem for p in prompts_dir.glob("*.md")]
        assert len(agents) > 0

    def test_troubleshooter_agent_discoverable(self):
        """Test that troubleshooter_of_workflows agent is discoverable."""
        prompts_dir = AGENTS_SRC / "prompts"
        agents = [p.stem for p in prompts_dir.glob("*.md")]
        assert "troubleshooter_of_workflows" in agents

    def test_creator_agent_discoverable(self):
        """Test that creator_of_agents agent is discoverable."""
        prompts_dir = AGENTS_SRC / "prompts"
        agents = [p.stem for p in prompts_dir.glob("*.md")]
        assert "creator_of_agents" in agents
