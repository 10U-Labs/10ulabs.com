import json
from pathlib import Path
import pytest


@pytest.fixture
def config():
    config_path = Path(__file__).parent.parent.parent / "src" / "claude_md" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        return json.load(f)
