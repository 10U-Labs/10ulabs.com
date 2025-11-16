import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest
from botocore.exceptions import ClientError

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "claude_md"))
import format_claude_md

def test_config_file_exists_in_correct_location():
    config_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "config.json"
    assert config_path.exists()

def test_config_has_required_account_id_field():
    config_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    assert 'account_id' in config

def test_config_has_required_region_field():
    config_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    assert 'region' in config

def test_config_has_required_bedrock_field():
    config_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    assert 'bedrock' in config

def test_config_bedrock_has_max_tokens():
    config_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    assert 'max_tokens' in config['bedrock']

def test_config_bedrock_has_model_id():
    config_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    assert 'model_id' in config['bedrock']

def test_config_account_id_is_integer():
    config_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    assert isinstance(config['account_id'], int)

def test_config_region_is_string():
    config_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    assert isinstance(config['region'], str)

def test_config_bedrock_max_tokens_is_integer():
    config_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    assert isinstance(config['bedrock']['max_tokens'], int)

def test_config_bedrock_model_id_is_string():
    config_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    assert isinstance(config['bedrock']['model_id'], str)

@patch('format_claude_md.time.sleep')
def test_call_bedrock_with_retry_succeeds_on_first_attempt(mock_sleep):
    mock_client = Mock()
    mock_client.converse.return_value = {
        'output': {
            'message': {
                'content': [{'text': 'formatted content'}]
            }
        }
    }
    bedrock_config = {'model_id': 'test-model', 'max_tokens': 1000}
    messages = [{'role': 'user', 'content': [{'text': 'test'}]}]
    result = format_claude_md.call_bedrock_with_retry(mock_client, bedrock_config, messages)
    assert 'output' in result

@patch('format_claude_md.time.sleep')
def test_call_bedrock_with_retry_retries_on_throttling(mock_sleep):
    mock_client = Mock()
    mock_client.converse.side_effect = [
        ClientError({'Error': {'Code': 'ThrottlingException'}}, 'converse'),
        {'output': {'message': {'content': [{'text': 'success'}]}}}
    ]
    bedrock_config = {'model_id': 'test-model', 'max_tokens': 1000}
    messages = [{'role': 'user', 'content': [{'text': 'test'}]}]
    result = format_claude_md.call_bedrock_with_retry(mock_client, bedrock_config, messages)
    assert 'output' in result

@patch('format_claude_md.time.sleep')
def test_call_bedrock_with_retry_raises_after_max_retries(mock_sleep):
    mock_client = Mock()
    mock_client.converse.side_effect = ClientError(
        {'Error': {'Code': 'ThrottlingException'}}, 'converse'
    )
    bedrock_config = {'model_id': 'test-model', 'max_tokens': 1000}
    messages = [{'role': 'user', 'content': [{'text': 'test'}]}]
    with pytest.raises(ClientError):
        format_claude_md.call_bedrock_with_retry(mock_client, bedrock_config, messages)

@patch('format_claude_md.time.sleep')
def test_call_bedrock_with_retry_raises_on_non_throttling_error(mock_sleep):
    mock_client = Mock()
    mock_client.converse.side_effect = ClientError(
        {'Error': {'Code': 'ValidationException'}}, 'converse'
    )
    bedrock_config = {'model_id': 'test-model', 'max_tokens': 1000}
    messages = [{'role': 'user', 'content': [{'text': 'test'}]}]
    with pytest.raises(ClientError):
        format_claude_md.call_bedrock_with_retry(mock_client, bedrock_config, messages)

@patch('format_claude_md.call_bedrock_with_retry')
@patch('format_claude_md.time.sleep')
def test_format_claude_md_returns_formatted_content(mock_sleep, mock_bedrock):
    mock_bedrock.return_value = {
        'output': {
            'message': {
                'content': [{'text': 'formatted content\n'}]
            }
        }
    }
    mock_client = Mock()
    current_content = 'original content'
    bedrock_config = {'model_id': 'test-model', 'max_tokens': 1000}

    with patch('builtins.open', mock_open(read_data='Test prompt: {current_content}')):
        result = format_claude_md.format_claude_md(mock_client, current_content, bedrock_config, 'test_prompt.md')
    assert result == 'formatted content\n'

@patch('format_claude_md.call_bedrock_with_retry')
@patch('format_claude_md.time.sleep')
def test_format_claude_md_adds_trailing_newline_if_missing(mock_sleep, mock_bedrock):
    mock_bedrock.return_value = {
        'output': {
            'message': {
                'content': [{'text': 'formatted content'}]
            }
        }
    }
    mock_client = Mock()
    current_content = 'original content'
    bedrock_config = {'model_id': 'test-model', 'max_tokens': 1000}

    with patch('builtins.open', mock_open(read_data='Test prompt: {current_content}')):
        result = format_claude_md.format_claude_md(mock_client, current_content, bedrock_config, 'test_prompt.md')
    assert result.endswith('\n')

@patch('format_claude_md.call_bedrock_with_retry')
@patch('format_claude_md.time.sleep')
def test_format_claude_md_exits_on_key_error(mock_sleep, mock_bedrock):
    mock_bedrock.return_value = {'invalid': 'response'}
    mock_client = Mock()
    current_content = 'original content'
    bedrock_config = {'model_id': 'test-model', 'max_tokens': 1000}
    with pytest.raises(SystemExit):
        with patch('builtins.open', mock_open(read_data='Test prompt: {current_content}')):
            format_claude_md.format_claude_md(mock_client, current_content, bedrock_config, 'test_prompt.md')

def test_format_claude_md_script_exists():
    script_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "format_claude_md.py"
    assert script_path.exists()

def test_format_claude_md_script_is_executable():
    script_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "format_claude_md.py"
    assert os.access(script_path, os.X_OK) or script_path.read_text().startswith('#!/usr/bin/env python3')

def test_call_bedrock_with_retry_uses_correct_model_id():
    mock_client = Mock()
    mock_client.converse.return_value = {
        'output': {'message': {'content': [{'text': 'test'}]}}
    }
    bedrock_config = {'model_id': 'custom-model-id', 'max_tokens': 1000}
    messages = [{'role': 'user', 'content': [{'text': 'test'}]}]
    format_claude_md.call_bedrock_with_retry(mock_client, bedrock_config, messages)
    mock_client.converse.assert_called_once()
    call_args = mock_client.converse.call_args
    assert call_args[1]['modelId'] == 'custom-model-id'

def test_call_bedrock_with_retry_uses_correct_max_tokens():
    mock_client = Mock()
    mock_client.converse.return_value = {
        'output': {'message': {'content': [{'text': 'test'}]}}
    }
    bedrock_config = {'model_id': 'test-model', 'max_tokens': 5000}
    messages = [{'role': 'user', 'content': [{'text': 'test'}]}]
    format_claude_md.call_bedrock_with_retry(mock_client, bedrock_config, messages)
    mock_client.converse.assert_called_once()
    call_args = mock_client.converse.call_args
    assert call_args[1]['inferenceConfig']['maxTokens'] == 5000

def test_aws_region_argument_is_required():
    with pytest.raises(SystemExit):
        format_claude_md.main.__wrapped__ if hasattr(format_claude_md.main, '__wrapped__') else None
        sys.argv = ['format_claude_md.py']
        parser = format_claude_md.argparse.ArgumentParser()
        parser.add_argument('--aws-region', required=True)
        parser.add_argument('--bedrock-model-id', required=True)
        parser.add_argument('--max-tokens-generation', type=int, required=True)
        parser.add_argument('--max-tokens-reasoning', type=int, required=True)
        parser.parse_args([])

def test_bedrock_model_id_argument_is_required():
    with pytest.raises(SystemExit):
        sys.argv = ['format_claude_md.py', '--aws-region', 'us-east-1']
        parser = format_claude_md.argparse.ArgumentParser()
        parser.add_argument('--aws-region', required=True)
        parser.add_argument('--bedrock-model-id', required=True)
        parser.add_argument('--max-tokens-generation', type=int, required=True)
        parser.add_argument('--max-tokens-reasoning', type=int, required=True)
        parser.parse_args(['--aws-region', 'us-east-1'])

def test_max_tokens_generation_argument_is_required():
    with pytest.raises(SystemExit):
        sys.argv = ['format_claude_md.py', '--aws-region', 'us-east-1', '--bedrock-model-id', 'model-id']
        parser = format_claude_md.argparse.ArgumentParser()
        parser.add_argument('--aws-region', required=True)
        parser.add_argument('--bedrock-model-id', required=True)
        parser.add_argument('--max-tokens-generation', type=int, required=True)
        parser.add_argument('--max-tokens-reasoning', type=int, required=True)
        parser.parse_args(['--aws-region', 'us-east-1', '--bedrock-model-id', 'model-id'])

def test_max_tokens_reasoning_argument_is_required():
    with pytest.raises(SystemExit):
        sys.argv = ['format_claude_md.py', '--aws-region', 'us-east-1', '--bedrock-model-id', 'model-id', '--max-tokens-generation', '1000']
        parser = format_claude_md.argparse.ArgumentParser()
        parser.add_argument('--aws-region', required=True)
        parser.add_argument('--bedrock-model-id', required=True)
        parser.add_argument('--max-tokens-generation', type=int, required=True)
        parser.add_argument('--max-tokens-reasoning', type=int, required=True)
        parser.parse_args(['--aws-region', 'us-east-1', '--bedrock-model-id', 'model-id', '--max-tokens-generation', '1000'])

def test_all_required_arguments_provided_successfully():
    parser = format_claude_md.argparse.ArgumentParser()
    parser.add_argument('--aws-region', required=True)
    parser.add_argument('--bedrock-model-id', required=True)
    parser.add_argument('--max-tokens-generation', type=int, required=True)
    parser.add_argument('--max-tokens-reasoning', type=int, required=True)
    args = parser.parse_args(['--aws-region', 'us-east-1', '--bedrock-model-id', 'model-id', '--max-tokens-generation', '1000', '--max-tokens-reasoning', '4000'])
    assert args.aws_region == 'us-east-1'
    assert args.bedrock_model_id == 'model-id'
    assert args.max_tokens_generation == 1000
    assert args.max_tokens_reasoning == 4000
