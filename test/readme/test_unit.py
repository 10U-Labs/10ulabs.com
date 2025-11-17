import json
import os
import sys
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

readme_path = Path(__file__).parent.parent.parent / "scripts" / "readme" / "readme.py"
spec = importlib.util.spec_from_file_location("readme", readme_path)
readme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readme)
sys.modules['readme'] = readme

split_text_by_words = readme.split_text_by_words
find_all_project_files = readme.find_all_project_files
read_all_project_files = readme.read_all_project_files
check_readme_should_be_updated = readme.check_readme_should_be_updated
generate_readme = readme.generate_readme

def test_split_text_by_words_returns_single_chunk_for_short_text():
    text = "Hello world"
    result = split_text_by_words(text, max_length=100)
    assert len(result) == 1


def test_split_text_by_words_returns_text_unchanged_for_short_text():
    text = "Hello world"
    result = split_text_by_words(text, max_length=100)
    assert result[0] == "Hello world"


def test_split_text_by_words_splits_long_text_into_chunks():
    text = " ".join(["word"] * 100)
    result = split_text_by_words(text, max_length=50)
    assert len(result) > 1


def test_split_text_by_words_respects_max_length():
    text = " ".join(["word"] * 100)
    result = split_text_by_words(text, max_length=50)
    assert all(len(chunk) <= 50 for chunk in result)


def test_split_text_by_words_preserves_all_words():
    text = "one two three four five"
    result = split_text_by_words(text, max_length=10)
    combined = " ".join(result)
    assert all(word in combined for word in ["one", "two", "three", "four", "five"])


def test_find_all_project_files_includes_readme_py():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "generator.py").write_text("content")
        Path(tmpdir, "other.py").write_text("content")
        result = find_all_project_files(tmpdir)
        assert any("generator.py" in f for f in result)


def test_find_all_project_files_includes_test_dir_when_provided():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = os.path.join(tmpdir, "src")
        test_dir = os.path.join(tmpdir, "test")
        os.makedirs(project_dir)
        os.makedirs(test_dir)
        Path(project_dir, "code.py").write_text("content")
        Path(test_dir, "test_something.py").write_text("content")
        result = find_all_project_files(project_dir, test_dir)
        assert any("test_something.py" in f for f in result)
        assert any("code.py" in f for f in result)


def test_find_all_project_files_includes_python_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "code.py").write_text("content")
        result = find_all_project_files(tmpdir)
        assert any("code.py" in f for f in result)


def test_find_all_project_files_includes_json_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "config.json").write_text("{}")
        result = find_all_project_files(tmpdir)
        assert any("config.json" in f for f in result)


def test_read_all_project_files_returns_non_empty_string():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "file.py").write_text("code")
        result = read_all_project_files(tmpdir)
        assert len(result) > 0


def test_read_all_project_files_includes_file_path_header():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "file.py").write_text("code")
        result = read_all_project_files(tmpdir)
        assert "File:" in result


def test_read_all_project_files_includes_file_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "file.py").write_text("unique_content")
        result = read_all_project_files(tmpdir)
        assert "unique_content" in result


def test_read_all_project_files_includes_separator():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "file.py").write_text("code")
        result = read_all_project_files(tmpdir)
        assert "=" * 60 in result


def test_read_all_project_files_returns_empty_for_no_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = read_all_project_files(tmpdir)
        assert result == ""


def test_check_readme_should_be_updated_returns_true_for_empty_readme():
    mock_client = Mock()
    result = check_readme_should_be_updated(
        mock_client, "files", "", {"model_id": "test", "max_tokens": 100}, "/tmp/prompt.md"
    )
    assert result is True


def test_check_readme_should_be_updated_returns_true_for_whitespace_readme():
    mock_client = Mock()
    result = check_readme_should_be_updated(
        mock_client, "files", "   \n  ", {"model_id": "test", "max_tokens": 100}, "/tmp/prompt.md"
    )
    assert result is True


@patch('readme.call_bedrock_with_retry')
def test_check_readme_should_be_updated_calls_bedrock_with_non_empty_readme(mock_bedrock):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("Prompt: {project_files} {current_readme}")
        prompt_file = f.name

    mock_bedrock.return_value = {
        'output': {'message': {'content': [{'text': '{"readme_should_be_updated": true, "reasoning": "test"}'}]}}
    }
    mock_client = Mock()

    result = check_readme_should_be_updated(
        mock_client, "files", "current", {"model_id": "test", "max_tokens": 100}, prompt_file
    )

    os.unlink(prompt_file)
    assert mock_bedrock.called


@patch('readme.call_bedrock_with_retry')
def test_check_readme_should_be_updated_parses_json_response(mock_bedrock):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("Prompt: {project_files} {current_readme}")
        prompt_file = f.name

    mock_bedrock.return_value = {
        'output': {'message': {'content': [{'text': '{"readme_should_be_updated": true, "reasoning": "test"}'}]}}
    }
    mock_client = Mock()

    result = check_readme_should_be_updated(
        mock_client, "files", "current", {"model_id": "test", "max_tokens": 100}, prompt_file
    )

    os.unlink(prompt_file)
    assert result is True


@patch('readme.call_bedrock_with_retry')
def test_check_readme_should_be_updated_handles_fallback_response(mock_bedrock):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("Prompt: {project_files} {current_readme}")
        prompt_file = f.name

    mock_bedrock.return_value = {
        'output': {'message': {'content': [{'text': 'true because reasons'}]}}
    }
    mock_client = Mock()

    result = check_readme_should_be_updated(
        mock_client, "files", "current", {"model_id": "test", "max_tokens": 100}, prompt_file
    )

    os.unlink(prompt_file)
    assert result is True


@patch('readme.call_bedrock_with_retry')
def test_generate_readme_returns_string(mock_bedrock):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("Prompt: {project_files}")
        prompt_file = f.name

    mock_bedrock.return_value = {
        'output': {'message': {'content': [{'text': 'Generated README content'}]}}
    }
    mock_client = Mock()

    result = generate_readme(
        mock_client, "files", {"model_id": "test", "max_tokens": 100}, prompt_file
    )

    os.unlink(prompt_file)
    assert isinstance(result, str)


@patch('readme.call_bedrock_with_retry')
def test_generate_readme_adds_trailing_newline(mock_bedrock):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("Prompt: {project_files}")
        prompt_file = f.name

    mock_bedrock.return_value = {
        'output': {'message': {'content': [{'text': 'Generated README content'}]}}
    }
    mock_client = Mock()

    result = generate_readme(
        mock_client, "files", {"model_id": "test", "max_tokens": 100}, prompt_file
    )

    os.unlink(prompt_file)
    assert result.endswith('\n')


@patch('readme.call_bedrock_with_retry')
def test_generate_readme_preserves_existing_trailing_newline(mock_bedrock):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("Prompt: {project_files}")
        prompt_file = f.name

    mock_bedrock.return_value = {
        'output': {'message': {'content': [{'text': 'Generated README content\n'}]}}
    }
    mock_client = Mock()

    result = generate_readme(
        mock_client, "files", {"model_id": "test", "max_tokens": 100}, prompt_file
    )

    os.unlink(prompt_file)
    assert result.count('\n') == 1


def test_find_all_project_files_includes_yaml_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "config.yaml").write_text("key: value")
        result = find_all_project_files(tmpdir)
        assert any("config.yaml" in f for f in result)


def test_find_all_project_files_returns_sorted_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "zebra.py").write_text("code")
        Path(tmpdir, "alpha.py").write_text("code")
        result = find_all_project_files(tmpdir)
        assert result == sorted(result)
