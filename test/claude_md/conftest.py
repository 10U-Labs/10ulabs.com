import json
from pathlib import Path
import boto3
import pytest


@pytest.fixture
def config():
    config_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def bedrock_client(config):
    return boto3.client('bedrock-runtime', region_name=config['region'])
