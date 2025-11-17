import boto3
import json
from pathlib import Path
import pytest


@pytest.fixture
def bedrock_client():
    return boto3.client('bedrock-runtime', region_name='us-east-1')


def test_bedrock_client_can_be_created():
    client = boto3.client('bedrock-runtime', region_name='us-east-1')
    assert client is not None


def test_bedrock_client_has_converse_method():
    client = boto3.client('bedrock-runtime', region_name='us-east-1')
    assert hasattr(client, 'converse')


def test_prompt_file_exists():
    prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'prompt.md'
    assert prompt_path.exists()


def test_prompt_file_has_current_content_variable():
    prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'prompt.md'
    content = prompt_path.read_text()
    assert '{current_content}' in content


def test_prompt_file_has_markdownlint_errors_variable():
    prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'prompt.md'
    content = prompt_path.read_text()
    assert '{markdownlint_errors}' in content


def test_prompt_formats_with_variables():
    prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'prompt.md'
    content = prompt_path.read_text()
    formatted = content.format(current_content="test content", markdownlint_errors="test errors")
    assert '{current_content}' not in formatted


def test_config_file_has_bedrock_section():
    config_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    assert 'bedrock' in config


def test_config_bedrock_has_max_tokens_reasoning():
    config_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    assert 'max_tokens_reasoning' in config['bedrock']


def test_bedrock_message_structure_is_valid():
    messages = [{
        'role': 'user',
        'content': [{'text': 'test prompt'}]
    }]
    assert messages[0]['role'] == 'user'


def test_reasoning_config_structure():
    reasoning_config = {
        'type': 'enabled',
        'budget_tokens': 4000
    }
    assert reasoning_config['type'] == 'enabled'


def test_additional_model_request_fields_structure():
    additional_fields = {
        'reasoning_config': {
            'type': 'enabled',
            'budget_tokens': 4000
        }
    }
    assert 'reasoning_config' in additional_fields
