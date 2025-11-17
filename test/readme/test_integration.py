import boto3
import json
import os
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


def test_bedrock_client_can_be_created():
    client = boto3.client('bedrock-runtime', region_name='us-east-1')
    assert client is not None


def test_bedrock_client_has_converse_method():
    client = boto3.client('bedrock-runtime', region_name='us-east-1')
    assert hasattr(client, 'converse')


def test_prompt_check_file_exists():
    prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_check.md'
    assert prompt_path.exists()


def test_prompt_update_file_exists():
    prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_update.md'
    assert prompt_path.exists()


def test_prompt_check_file_has_project_files_variable():
    prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_check.md'
    content = prompt_path.read_text()
    assert '{project_files}' in content


def test_prompt_check_file_has_current_readme_variable():
    prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_check.md'
    content = prompt_path.read_text()
    assert '{current_readme}' in content


def test_prompt_update_file_has_project_files_variable():
    prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_update.md'
    content = prompt_path.read_text()
    assert '{project_files}' in content


def test_prompt_check_formats_with_variables():
    prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_check.md'
    content = prompt_path.read_text()
    formatted = content.format(project_files="test files", current_readme="test readme")
    assert '{project_files}' not in formatted


def test_prompt_update_formats_with_variables():
    prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'readme' / 'prompt_update.md'
    content = prompt_path.read_text()
    formatted = content.format(project_files="test files")
    assert '{project_files}' not in formatted


def test_output_file_can_be_written():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("readme_should_be_updated=true\n")
        output_file = f.name

    content = Path(output_file).read_text()
    os.unlink(output_file)
    assert "readme_should_be_updated=true" in content
