import os
import subprocess
import tempfile
from pathlib import Path


def test_format_claude_md_runs_successfully(config):
    model_id = config['bedrock']['model_id']
    max_tokens = config['bedrock']['max_tokens']
    max_tokens_reasoning = config['bedrock']['max_tokens_reasoning']
    region = config['region']

    test_content = "# Test\n\nThis is a test file.\n"

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "CLAUDE.md"
        test_file.write_text(test_content, encoding='utf-8')

        script_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "format_claude_md.py"
        result = subprocess.run(
            [
                'python', str(script_path),
                '--aws-region', region,
                '--bedrock-model-id', model_id,
                '--max-tokens', str(max_tokens),
                '--max-tokens-reasoning', str(max_tokens_reasoning)
            ],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=120,
            check=False
        )

        assert result.returncode == 0


def test_format_claude_md_creates_formatted_output(config):
    model_id = config['bedrock']['model_id']
    max_tokens = config['bedrock']['max_tokens']
    max_tokens_reasoning = config['bedrock']['max_tokens_reasoning']
    region = config['region']

    test_content = "#Test\nNo space after hash."

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "CLAUDE.md"
        test_file.write_text(test_content, encoding='utf-8')

        script_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "format_claude_md.py"
        result = subprocess.run(
            [
                'python', str(script_path),
                '--aws-region', region,
                '--bedrock-model-id', model_id,
                '--max-tokens', str(max_tokens),
                '--max-tokens-reasoning', str(max_tokens_reasoning)
            ],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=120,
            check=False
        )

        assert result.returncode == 0
        formatted_content = test_file.read_text(encoding='utf-8')
        assert len(formatted_content) > 0


def test_format_claude_md_preserves_trailing_newline(config):
    model_id = config['bedrock']['model_id']
    max_tokens = config['bedrock']['max_tokens']
    max_tokens_reasoning = config['bedrock']['max_tokens_reasoning']
    region = config['region']

    test_content = "# Test\n\nContent\n"

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "CLAUDE.md"
        test_file.write_text(test_content, encoding='utf-8')

        script_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "format_claude_md.py"
        result = subprocess.run(
            [
                'python', str(script_path),
                '--aws-region', region,
                '--bedrock-model-id', model_id,
                '--max-tokens', str(max_tokens),
                '--max-tokens-reasoning', str(max_tokens_reasoning)
            ],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=120,
            check=False
        )

        assert result.returncode == 0
        formatted_content = test_file.read_text(encoding='utf-8')
        assert formatted_content.endswith('\n')
