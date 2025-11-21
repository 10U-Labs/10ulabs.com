import json
from pathlib import Path
import pytest


@pytest.fixture
def config():
    config_path = Path(__file__).parent.parent.parent / "src" / "gmail" / "config.json"
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def gmail_config_path():
    return Path(__file__).parent.parent.parent / "src" / "gmail" / "config.json"
