from pathlib import Path
import pytest

@pytest.fixture
def project_root():
    return Path(__file__).parent.parent.parent

@pytest.fixture
def script_dir(project_root):
    return project_root / 'scripts' / 'transform_to_compliant_markdown'

@pytest.fixture
def script_path(script_dir):
    return script_dir / 'transform_to_compliant_markdown.py'

@pytest.fixture
def config_path(script_dir):
    return script_dir / 'config.json'

@pytest.fixture
def prompt_path(script_dir):
    return script_dir / 'prompt.md'
