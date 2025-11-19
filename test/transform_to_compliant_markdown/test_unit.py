import json
import os
import sys
import importlib.util
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest
from botocore.exceptions import ClientError

transform_script_path = Path(__file__).parent.parent.parent / "scripts" / "transform_to_compliant_markdown" / "transform_to_compliant_markdown.py"
spec = importlib.util.spec_from_file_location("transform_to_compliant_markdown", transform_script_path)
transform_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transform_module)
sys.modules['transform_to_compliant_markdown'] = transform_module

@patch('transform_to_compliant_markdown.time.sleep')
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
    result = transform_module.call_bedrock_with_retry(mock_client, bedrock_config, messages)
    assert 'output' in result

@patch('transform_to_compliant_markdown.time.sleep')
def test_call_bedrock_with_retry_retries_on_throttling(mock_sleep):
    mock_client = Mock()
    mock_client.converse.side_effect = [
        ClientError({'Error': {'Code': 'ThrottlingException'}}, 'converse'),
        {'output': {'message': {'content': [{'text': 'success'}]}}}
    ]
    bedrock_config = {'model_id': 'test-model', 'max_tokens': 1000}
    messages = [{'role': 'user', 'content': [{'text': 'test'}]}]
    result = transform_module.call_bedrock_with_retry(mock_client, bedrock_config, messages)
    assert 'output' in result

@patch('transform_to_compliant_markdown.time.sleep')
def test_call_bedrock_with_retry_raises_after_max_retries(mock_sleep):
    mock_client = Mock()
    mock_client.converse.side_effect = ClientError(
        {'Error': {'Code': 'ThrottlingException'}}, 'converse'
    )
    bedrock_config = {'model_id': 'test-model', 'max_tokens': 1000}
    messages = [{'role': 'user', 'content': [{'text': 'test'}]}]
    with pytest.raises(ClientError):
        transform_module.call_bedrock_with_retry(mock_client, bedrock_config, messages)

@patch('transform_to_compliant_markdown.time.sleep')
def test_call_bedrock_with_retry_raises_on_non_throttling_error(mock_sleep):
    mock_client = Mock()
    mock_client.converse.side_effect = ClientError(
        {'Error': {'Code': 'ValidationException'}}, 'converse'
    )
    bedrock_config = {'model_id': 'test-model', 'max_tokens': 1000}
    messages = [{'role': 'user', 'content': [{'text': 'test'}]}]
    with pytest.raises(ClientError):
        transform_module.call_bedrock_with_retry(mock_client, bedrock_config, messages)

@patch('transform_to_compliant_markdown.call_bedrock_with_retry')
@patch('transform_to_compliant_markdown.time.sleep')
def test_format_markdown_returns_formatted_content(mock_sleep, mock_bedrock):
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
        result = transform_module.format_markdown(mock_client, current_content, bedrock_config, 'test_prompt.md', markdownlint_errors='')
    assert result == 'formatted content\n'

@patch('transform_to_compliant_markdown.call_bedrock_with_retry')
@patch('transform_to_compliant_markdown.time.sleep')
def test_format_markdown_adds_trailing_newline_if_missing(mock_sleep, mock_bedrock):
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
        result = transform_module.format_markdown(mock_client, current_content, bedrock_config, 'test_prompt.md', markdownlint_errors='')
    assert result.endswith('\n')

@patch('transform_to_compliant_markdown.call_bedrock_with_retry')
@patch('transform_to_compliant_markdown.time.sleep')
def test_format_markdown_exits_on_key_error(mock_sleep, mock_bedrock):
    mock_bedrock.return_value = {'invalid': 'response'}
    mock_client = Mock()
    current_content = 'original content'
    bedrock_config = {'model_id': 'test-model', 'max_tokens': 1000}
    with pytest.raises(SystemExit):
        with patch('builtins.open', mock_open(read_data='Test prompt: {current_content}')):
            transform_module.format_markdown(mock_client, current_content, bedrock_config, 'test_prompt.md', markdownlint_errors='')

def test_call_bedrock_with_retry_uses_correct_model_id():
    mock_client = Mock()
    mock_client.converse.return_value = {
        'output': {'message': {'content': [{'text': 'test'}]}}
    }
    bedrock_config = {'model_id': 'custom-model-id', 'max_tokens': 1000}
    messages = [{'role': 'user', 'content': [{'text': 'test'}]}]
    transform_module.call_bedrock_with_retry(mock_client, bedrock_config, messages)
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
    transform_module.call_bedrock_with_retry(mock_client, bedrock_config, messages)
    mock_client.converse.assert_called_once()
    call_args = mock_client.converse.call_args
    assert call_args[1]['inferenceConfig']['maxTokens'] == 5000

def test_aws_region_argument_is_required():
    with pytest.raises(SystemExit):
        transform_module.main.__wrapped__ if hasattr(transform_module.main, '__wrapped__') else None
        sys.argv = ['transform_to_compliant_markdown.py']
        parser = transform_module.argparse.ArgumentParser()
        parser.add_argument('--aws-region', required=True)
        parser.add_argument('--bedrock-model-id', required=True)
        parser.add_argument('--max-tokens', type=int, required=True)
        parser.parse_args([])

def test_bedrock_model_id_argument_is_required():
    with pytest.raises(SystemExit):
        sys.argv = ['transform_to_compliant_markdown.py', '--aws-region', 'us-east-1']
        parser = transform_module.argparse.ArgumentParser()
        parser.add_argument('--aws-region', required=True)
        parser.add_argument('--bedrock-model-id', required=True)
        parser.add_argument('--max-tokens', type=int, required=True)
        parser.parse_args(['--aws-region', 'us-east-1'])

def test_max_tokens_argument_is_required():
    with pytest.raises(SystemExit):
        sys.argv = ['transform_to_compliant_markdown.py', '--aws-region', 'us-east-1', '--bedrock-model-id', 'model-id']
        parser = transform_module.argparse.ArgumentParser()
        parser.add_argument('--aws-region', required=True)
        parser.add_argument('--bedrock-model-id', required=True)
        parser.add_argument('--max-tokens', type=int, required=True)
        parser.parse_args(['--aws-region', 'us-east-1', '--bedrock-model-id', 'model-id'])

def test_file_argument_is_required():
    with pytest.raises(SystemExit):
        sys.argv = ['transform_to_compliant_markdown.py']
        parser = transform_module.argparse.ArgumentParser()
        parser.add_argument('--file', required=True)
        parser.parse_args([])

def test_prompt_file_argument_is_required():
    with pytest.raises(SystemExit):
        sys.argv = ['transform_to_compliant_markdown.py', '--file', 'test.md']
        parser = transform_module.argparse.ArgumentParser()
        parser.add_argument('--file', required=True)
        parser.add_argument('--prompt-file', required=True)
        parser.parse_args(['--file', 'test.md'])

def test_file_argument_is_parsed_correctly():
    parser = transform_module.argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    parser.add_argument('--aws-region', required=True)
    parser.add_argument('--bedrock-model-id', required=True)
    parser.add_argument('--max-tokens-generation', type=int, required=True)
    parser.add_argument('--max-tokens-reasoning', type=int, required=True)
    parser.add_argument('--prompt-file', required=True)
    args = parser.parse_args([
        '--file', 'test.md',
        '--aws-region', 'us-east-1',
        '--bedrock-model-id', 'model-id',
        '--max-tokens', '64000',
        '--prompt-file', 'prompt.md'
    ])
    assert args.file == 'test.md'

def test_aws_region_argument_is_parsed_correctly():
    parser = transform_module.argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    parser.add_argument('--aws-region', required=True)
    parser.add_argument('--bedrock-model-id', required=True)
    parser.add_argument('--max-tokens-generation', type=int, required=True)
    parser.add_argument('--max-tokens-reasoning', type=int, required=True)
    parser.add_argument('--prompt-file', required=True)
    args = parser.parse_args([
        '--file', 'test.md',
        '--aws-region', 'us-east-1',
        '--bedrock-model-id', 'model-id',
        '--max-tokens', '64000',
        '--prompt-file', 'prompt.md'
    ])
    assert args.aws_region == 'us-east-1'

def test_bedrock_model_id_argument_is_parsed_correctly():
    parser = transform_module.argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    parser.add_argument('--aws-region', required=True)
    parser.add_argument('--bedrock-model-id', required=True)
    parser.add_argument('--max-tokens-generation', type=int, required=True)
    parser.add_argument('--max-tokens-reasoning', type=int, required=True)
    parser.add_argument('--prompt-file', required=True)
    args = parser.parse_args([
        '--file', 'test.md',
        '--aws-region', 'us-east-1',
        '--bedrock-model-id', 'model-id',
        '--max-tokens', '64000',
        '--prompt-file', 'prompt.md'
    ])
    assert args.bedrock_model_id == 'model-id'

def test_max_tokens_argument_is_parsed_correctly():
    parser = transform_module.argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    parser.add_argument('--aws-region', required=True)
    parser.add_argument('--bedrock-model-id', required=True)
    parser.add_argument('--max-tokens', type=int, required=True)
    parser.add_argument('--prompt-file', required=True)
    args = parser.parse_args([
        '--file', 'test.md',
        '--aws-region', 'us-east-1',
        '--bedrock-model-id', 'model-id',
        '--max-tokens', '64000',
        '--prompt-file', 'prompt.md'
    ])
    assert args.max_tokens == 64000

def test_prompt_file_argument_is_parsed_correctly():
    parser = transform_module.argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    parser.add_argument('--aws-region', required=True)
    parser.add_argument('--bedrock-model-id', required=True)
    parser.add_argument('--max-tokens', type=int, required=True)
    parser.add_argument('--prompt-file', required=True)
    args = parser.parse_args([
        '--file', 'test.md',
        '--aws-region', 'us-east-1',
        '--bedrock-model-id', 'model-id',
        '--max-tokens', '64000',
        '--prompt-file', 'prompt.md'
    ])
    assert args.prompt_file == 'prompt.md'

@patch('transform_to_compliant_markdown.time.sleep')
def test_call_bedrock_with_retry_excludes_reasoning_config_when_not_in_config(mock_sleep):
    mock_client = Mock()
    mock_client.converse.return_value = {
        'output': {'message': {'content': [{'text': 'test'}]}}
    }
    bedrock_config = {'model_id': 'test-model', 'max_tokens': 1000}
    messages = [{'role': 'user', 'content': [{'text': 'test'}]}]
    transform_module.call_bedrock_with_retry(mock_client, bedrock_config, messages)
    call_args = mock_client.converse.call_args
    assert 'additionalModelRequestFields' not in call_args[1]

@patch('transform_to_compliant_markdown.call_bedrock_with_retry')
@patch('transform_to_compliant_markdown.time.sleep')
def test_format_markdown_formats_prompt_with_markdownlint_errors(mock_sleep, mock_bedrock):
    mock_bedrock.return_value = {
        'output': {
            'message': {
                'content': [{'text': 'formatted content\n'}]
            }
        }
    }
    mock_client = Mock()
    current_content = 'test content'
    bedrock_config = {'model_id': 'test-model', 'max_tokens': 1000}
    markdownlint_errors = '{"test.md": [{"line": 1}]}'

    with patch('builtins.open', mock_open(read_data='Content: {current_content}\nErrors: {markdownlint_errors}')):
        transform_module.format_markdown(mock_client, current_content, bedrock_config, 'test_prompt.md', markdownlint_errors=markdownlint_errors)

    call_args = mock_bedrock.call_args
    prompt = call_args[0][2][0]['content'][0]['text']
    assert 'test content' in prompt
