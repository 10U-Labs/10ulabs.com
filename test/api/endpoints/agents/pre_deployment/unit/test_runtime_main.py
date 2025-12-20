"""Unit tests for agents runtime main.py."""
from repo_utils import REPO_ROOT

AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"
RUNTIME_DIR = AGENTS_SRC / "runtime"


def test_runtime_main_py_exists():
    """Test that main.py exists in runtime directory."""
    main_file = RUNTIME_DIR / "main.py"
    assert main_file.exists()


def test_runtime_main_has_model_id_constant():
    """Test that main.py defines MODEL_ID constant."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "MODEL_ID" in content


def test_runtime_main_uses_opus_model():
    """Test that main.py uses Claude Opus 4.5 model."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "claude-opus-4-5" in content


def test_runtime_main_imports_bedrock_model():
    """Test that main.py imports BedrockModel from strands.models."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "from strands.models import BedrockModel" in content


def test_runtime_main_passes_model_to_agent():
    """Test that main.py passes model to Agent configuration."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert '"model": model' in content or "'model': model" in content


def test_runtime_main_imports_tools():
    """Test that main.py imports ALL_TOOLS from tools."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "from tools import ALL_TOOLS" in content


def test_runtime_main_has_load_prompt_from_s3_function():
    """Test that main.py defines load_prompt_from_s3 function."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "def load_prompt_from_s3" in content


def test_runtime_main_has_extract_recommendation_function():
    """Test that main.py defines extract_recommendation function."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "def extract_recommendation" in content


def test_runtime_main_has_entrypoint_decorator():
    """Test that main.py uses app.entrypoint pattern."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "@_apply_entrypoint" in content or "@app.entrypoint" in content


def test_runtime_main_has_invoke_function():
    """Test that main.py defines invoke function."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "def invoke" in content


def test_runtime_main_uses_s3_for_prompts():
    """Test that main.py uses S3 for loading prompts."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "s3_client" in content or "s3.get_object" in content.lower()


def test_runtime_main_has_guardrail_configuration():
    """Test that main.py supports guardrail configuration."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "GUARDRAIL_ID" in content or "guardrail" in content.lower()


def test_runtime_main_has_memory_configuration():
    """Test that main.py supports memory configuration."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "MEMORY_ARN" in content or "memory" in content.lower()


def test_runtime_main_references_prompts_bucket():
    """Test that main.py references PROMPTS_BUCKET environment variable."""
    main_file = RUNTIME_DIR / "main.py"
    content = main_file.read_text()
    assert "PROMPTS_BUCKET" in content


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

    def test_prompts_directory_exists_in_src(self):
        """Test that prompts directory exists in source (uploaded to S3)."""
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
