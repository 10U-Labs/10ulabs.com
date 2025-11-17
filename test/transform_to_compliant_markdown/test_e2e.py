import boto3
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from botocore.exceptions import NoCredentialsError, ClientError
import pytest


def check_aws_credentials():
    try:
        client = boto3.client('bedrock-runtime', region_name='us-east-1')
        return True
    except (NoCredentialsError, ClientError):
        return False


pytestmark = pytest.mark.skipif(
    not check_aws_credentials(),
    reason="AWS credentials not available via OIDC"
)


@pytest.fixture
def bedrock_client():
    return boto3.client('bedrock-runtime', region_name='us-east-1')


@pytest.fixture
def temp_claude_md():
    with tempfile.TemporaryDirectory() as tmpdir:
        original_dir = os.getcwd()
        os.chdir(tmpdir)
        claude_md = Path(tmpdir) / 'CLAUDE.md'
        claude_md.write_text('# Test\nThis is a test CLAUDE.md file with a very long line that exceeds the markdownlint line length limit of 80 characters and should be fixed.\n')
        yield tmpdir
        os.chdir(original_dir)


def test_script_formats_claude_md_with_markdownlint_errors(temp_claude_md):
    script_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'transform_to_compliant_markdown.py'
    prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'prompt.md'

    markdownlint_errors = '{"file.md": [{"lineNumber": 2, "ruleNames": ["MD013"], "ruleDescription": "Line length"}]}'

    result = subprocess.run([
        sys.executable,
        str(script_path),
        '--file', 'CLAUDE.md',
        '--aws-region', 'us-east-1',
        '--bedrock-model-id', 'us.anthropic.claude-sonnet-4-20250514-v1:0',
        '--max-tokens-reasoning', '4000',
        '--max-tokens-generation', '16000',
        '--prompt-file', str(prompt_path),
        '--markdownlint-errors', markdownlint_errors
    ], capture_output=True, text=True, cwd=temp_claude_md)

    assert result.returncode == 0


def test_script_formats_claude_md_without_markdownlint_errors(temp_claude_md):
    script_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'transform_to_compliant_markdown.py'
    prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'prompt.md'

    result = subprocess.run([
        sys.executable,
        str(script_path),
        '--file', 'CLAUDE.md',
        '--aws-region', 'us-east-1',
        '--bedrock-model-id', 'us.anthropic.claude-sonnet-4-20250514-v1:0',
        '--max-tokens-reasoning', '4000',
        '--max-tokens-generation', '16000',
        '--prompt-file', str(prompt_path)
    ], capture_output=True, text=True, cwd=temp_claude_md)

    assert result.returncode == 0


def test_generated_output_ends_with_newline(temp_claude_md):
    script_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'transform_to_compliant_markdown.py'
    prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'prompt.md'

    result = subprocess.run([
        sys.executable,
        str(script_path),
        '--file', 'CLAUDE.md',
        '--aws-region', 'us-east-1',
        '--bedrock-model-id', 'us.anthropic.claude-sonnet-4-20250514-v1:0',
        '--max-tokens-reasoning', '4000',
        '--max-tokens-generation', '16000',
        '--prompt-file', str(prompt_path)
    ], capture_output=True, text=True, cwd=temp_claude_md)

    assert result.returncode == 0
    claude_md = Path(temp_claude_md) / 'CLAUDE.md'
    content = claude_md.read_text()
    assert content.endswith('\n')


def test_script_exits_with_error_when_claude_md_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'transform_to_compliant_markdown.py'
        prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'prompt.md'

        result = subprocess.run([
            sys.executable,
            str(script_path),
            '--file', 'CLAUDE.md',
            '--aws-region', 'us-east-1',
            '--bedrock-model-id', 'us.anthropic.claude-sonnet-4-20250514-v1:0',
            '--max-tokens-reasoning', '4000',
            '--max-tokens-generation', '16000',
            '--prompt-file', str(prompt_path)
        ], capture_output=True, text=True, cwd=tmpdir)

        assert result.returncode == 1


def test_script_works_with_any_markdown_filename():
    with tempfile.TemporaryDirectory() as tmpdir:
        original_dir = os.getcwd()
        os.chdir(tmpdir)

        test_md = Path(tmpdir) / 'README.md'
        test_md.write_text('# Test\nThis is a test markdown file.\n')

        script_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'transform_to_compliant_markdown.py'
        prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'prompt.md'

        result = subprocess.run([
            sys.executable,
            str(script_path),
            '--file', 'README.md',
            '--aws-region', 'us-east-1',
            '--bedrock-model-id', 'us.anthropic.claude-sonnet-4-20250514-v1:0',
            '--max-tokens-reasoning', '4000',
            '--max-tokens-generation', '16000',
            '--prompt-file', str(prompt_path)
        ], capture_output=True, text=True, cwd=tmpdir)

        os.chdir(original_dir)

        assert result.returncode == 0
