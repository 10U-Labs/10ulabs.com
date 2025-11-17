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
def temp_test_md():
    with tempfile.TemporaryDirectory() as tmpdir:
        original_dir = os.getcwd()
        os.chdir(tmpdir)
        test_md = Path(tmpdir) / 'test.md'
        test_md.write_text('# Test\nThis is a test markdown file with a very long line that exceeds the markdownlint line length limit of 80 characters and should be fixed.\n')
        yield tmpdir
        os.chdir(original_dir)


def test_script_formats_markdown_with_markdownlint_errors(temp_test_md, script_path, prompt_path, config):
    markdownlint_errors = '{"file.md": [{"lineNumber": 2, "ruleNames": ["MD013"], "ruleDescription": "Line length"}]}'

    result = subprocess.run([
        sys.executable,
        str(script_path),
        '--file', 'test.md',
        '--aws-region', config['region'],
        '--bedrock-model-id', config['bedrock']['model_id'],
        '--max-tokens-reasoning', str(config['bedrock']['max_tokens_reasoning']),
        '--max-tokens-generation', str(config['bedrock']['max_tokens_generation']),
        '--prompt-file', str(prompt_path),
        '--markdownlint-errors', markdownlint_errors
    ], capture_output=True, text=True, cwd=temp_test_md)

    assert result.returncode == 0


def test_script_formats_markdown_without_markdownlint_errors(temp_test_md, script_path, prompt_path, config):
    result = subprocess.run([
        sys.executable,
        str(script_path),
        '--file', 'test.md',
        '--aws-region', config['region'],
        '--bedrock-model-id', config['bedrock']['model_id'],
        '--max-tokens-reasoning', str(config['bedrock']['max_tokens_reasoning']),
        '--max-tokens-generation', str(config['bedrock']['max_tokens_generation']),
        '--prompt-file', str(prompt_path)
    ], capture_output=True, text=True, cwd=temp_test_md)

    assert result.returncode == 0


def test_generated_output_ends_with_newline(temp_test_md, script_path, prompt_path, config):
    result = subprocess.run([
        sys.executable,
        str(script_path),
        '--file', 'test.md',
        '--aws-region', config['region'],
        '--bedrock-model-id', config['bedrock']['model_id'],
        '--max-tokens-reasoning', str(config['bedrock']['max_tokens_reasoning']),
        '--max-tokens-generation', str(config['bedrock']['max_tokens_generation']),
        '--prompt-file', str(prompt_path)
    ], capture_output=True, text=True, cwd=temp_test_md)

    assert result.returncode == 0
    test_md = Path(temp_test_md) / 'test.md'
    content = test_md.read_text()
    assert content.endswith('\n')


def test_script_exits_with_error_when_file_missing(script_path, prompt_path, config):
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run([
            sys.executable,
            str(script_path),
            '--file', 'nonexistent.md',
            '--aws-region', config['region'],
            '--bedrock-model-id', config['bedrock']['model_id'],
            '--max-tokens-reasoning', str(config['bedrock']['max_tokens_reasoning']),
            '--max-tokens-generation', str(config['bedrock']['max_tokens_generation']),
            '--prompt-file', str(prompt_path)
        ], capture_output=True, text=True, cwd=tmpdir)

        assert result.returncode == 1


def test_script_works_with_any_markdown_filename(script_path, prompt_path, config):
    with tempfile.TemporaryDirectory() as tmpdir:
        original_dir = os.getcwd()
        os.chdir(tmpdir)

        test_md = Path(tmpdir) / 'README.md'
        test_md.write_text('# Test\nThis is a test markdown file.\n')

        result = subprocess.run([
            sys.executable,
            str(script_path),
            '--file', 'README.md',
            '--aws-region', config['region'],
            '--bedrock-model-id', config['bedrock']['model_id'],
            '--max-tokens-reasoning', str(config['bedrock']['max_tokens_reasoning']),
            '--max-tokens-generation', str(config['bedrock']['max_tokens_generation']),
            '--prompt-file', str(prompt_path)
        ], capture_output=True, text=True, cwd=tmpdir)

        os.chdir(original_dir)

        assert result.returncode == 0
