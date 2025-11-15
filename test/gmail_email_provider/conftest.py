import json
from pathlib import Path
import pytest


@pytest.fixture
def config():
    config_path = Path(__file__).parent.parent.parent / "src" / "gmail_email_provider" / "config.json"
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def gmail_config_path():
    return Path(__file__).parent.parent.parent / "src" / "gmail_email_provider" / "config.json"


@pytest.fixture
def gmail_stack_path():
    return Path(__file__).parent.parent.parent / "src" / "gmail_email_provider" / "stack.py"


@pytest.fixture
def domain_config_path():
    return Path(__file__).parent.parent.parent / "src" / "cloudtrail_and_domain_name" / "config.json"


@pytest.fixture
def domain_stack_path():
    return Path(__file__).parent.parent.parent / "src" / "cloudtrail_and_domain_name" / "stack.py"
