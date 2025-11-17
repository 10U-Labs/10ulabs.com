import boto3
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def bedrock_client():
    return boto3.client('bedrock-runtime', region_name='us-east-1')


@pytest.fixture
def test_project_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "stack.py").write_text("class TestStack: pass")
        Path(tmpdir, "config.json").write_text('{"test": "value"}')
        yield tmpdir


def test_check_workflow_writes_output_file_when_readme_missing(test_project_dir):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as output_file:
        output_path = output_file.name

    script_path = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'readme.py'
    prompt_check = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_check.md'
    prompt_update = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_update.md'

    result = subprocess.run([
        sys.executable,
        str(script_path),
        '--check',
        '--project-dir', test_project_dir,
        '--aws-region', 'us-east-1',
        '--bedrock-model-id', 'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
        '--max-tokens-reasoning', '4096',
        '--max-tokens-generation', '16384',
        '--prompt-check', str(prompt_check),
        '--prompt-update', str(prompt_update),
        '--output-file', output_path
    ], capture_output=True, text=True)

    content = Path(output_path).read_text()
    os.unlink(output_path)

    assert 'readme_should_be_updated=' in content


def test_update_workflow_creates_readme_file(test_project_dir):
    script_path = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'readme.py'
    prompt_check = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_check.md'
    prompt_update = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_update.md'

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as output_file:
        output_path = output_file.name

    result = subprocess.run([
        sys.executable,
        str(script_path),
        '--update',
        '--project-dir', test_project_dir,
        '--aws-region', 'us-east-1',
        '--bedrock-model-id', 'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
        '--max-tokens-reasoning', '4096',
        '--max-tokens-generation', '16384',
        '--prompt-check', str(prompt_check),
        '--prompt-update', str(prompt_update),
        '--output-file', output_path
    ], capture_output=True, text=True)

    readme_path = Path(test_project_dir) / 'README.md'
    os.unlink(output_path)

    assert readme_path.exists()


def test_generated_readme_contains_markdown(test_project_dir):
    script_path = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'readme.py'
    prompt_check = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_check.md'
    prompt_update = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_update.md'

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as output_file:
        output_path = output_file.name

    subprocess.run([
        sys.executable,
        str(script_path),
        '--update',
        '--project-dir', test_project_dir,
        '--aws-region', 'us-east-1',
        '--bedrock-model-id', 'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
        '--max-tokens-reasoning', '4096',
        '--max-tokens-generation', '16384',
        '--prompt-check', str(prompt_check),
        '--prompt-update', str(prompt_update),
        '--output-file', output_path
    ], capture_output=True, text=True)

    readme_path = Path(test_project_dir) / 'README.md'
    content = readme_path.read_text()
    os.unlink(output_path)

    assert '#' in content


def test_generated_readme_ends_with_newline(test_project_dir):
    script_path = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'readme.py'
    prompt_check = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_check.md'
    prompt_update = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_update.md'

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as output_file:
        output_path = output_file.name

    subprocess.run([
        sys.executable,
        str(script_path),
        '--update',
        '--project-dir', test_project_dir,
        '--aws-region', 'us-east-1',
        '--bedrock-model-id', 'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
        '--max-tokens-reasoning', '4096',
        '--max-tokens-generation', '16384',
        '--prompt-check', str(prompt_check),
        '--prompt-update', str(prompt_update),
        '--output-file', output_path
    ], capture_output=True, text=True)

    readme_path = Path(test_project_dir) / 'README.md'
    content = readme_path.read_text()
    os.unlink(output_path)

    assert content.endswith('\n')


def test_check_workflow_with_actual_prompt_files(test_project_dir):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as output_file:
        output_path = output_file.name

    script_path = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'readme.py'
    prompt_check = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_check.md'
    prompt_update = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_update.md'

    result = subprocess.run([
        sys.executable,
        str(script_path),
        '--check',
        '--project-dir', test_project_dir,
        '--aws-region', 'us-east-1',
        '--bedrock-model-id', 'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
        '--max-tokens-reasoning', '4096',
        '--max-tokens-generation', '16384',
        '--prompt-check', str(prompt_check),
        '--prompt-update', str(prompt_update),
        '--output-file', output_path
    ], capture_output=True, text=True)

    os.unlink(output_path)

    assert result.returncode == 0
