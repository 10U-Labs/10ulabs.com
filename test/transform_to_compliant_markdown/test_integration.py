import json
import os
from pathlib import Path


def test_config_file_exists_in_correct_location():
    config_path = Path(__file__).parent.parent.parent / "scripts" / "transform_to_compliant_markdown" / "config.json"
    assert config_path.exists()

def test_config_account_id_is_integer():
    config_path = Path(__file__).parent.parent.parent / "scripts" / "transform_to_compliant_markdown" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    assert isinstance(config['account_id'], int)

def test_config_region_is_string():
    config_path = Path(__file__).parent.parent.parent / "scripts" / "transform_to_compliant_markdown" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    assert isinstance(config['region'], str)

def test_config_bedrock_max_tokens_is_integer():
    config_path = Path(__file__).parent.parent.parent / "scripts" / "transform_to_compliant_markdown" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    assert isinstance(config['bedrock']['max_tokens'], int)

def test_config_bedrock_model_id_is_string():
    config_path = Path(__file__).parent.parent.parent / "scripts" / "transform_to_compliant_markdown" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    assert isinstance(config['bedrock']['model_id'], str)

def test_transform_script_exists():
    script_path = Path(__file__).parent.parent.parent / "scripts" / "transform_to_compliant_markdown" / "transform_to_compliant_markdown.py"
    assert script_path.exists()

def test_transform_script_is_executable():
    script_path = Path(__file__).parent.parent.parent / "scripts" / "transform_to_compliant_markdown" / "transform_to_compliant_markdown.py"
    assert os.access(script_path, os.X_OK) or script_path.read_text().startswith('#!/usr/bin/env python3')

def test_prompt_file_exists():
    prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'prompt.md'
    assert prompt_path.exists()

def test_prompt_formats_with_variables():
    prompt_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'prompt.md'
    content = prompt_path.read_text()
    formatted = content.format(current_content="test content", markdownlint_errors="test errors")
    assert '{current_content}' not in formatted

def test_config_bedrock_has_max_tokens_reasoning():
    config_path = Path(__file__).parent.parent.parent / 'scripts' / 'transform_to_compliant_markdown' / 'config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    assert 'max_tokens_reasoning' in config['bedrock']
