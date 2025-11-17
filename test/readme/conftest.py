from pathlib import Path
import pytest


@pytest.fixture
def readme_script_path():
    return Path(__file__).parent.parent.parent / "scripts" / "readme" / "readme.py"


@pytest.fixture
def prompt_check_path():
    return Path(__file__).parent.parent.parent / "scripts" / "readme" / "prompt_check.md"


@pytest.fixture
def prompt_update_path():
    return Path(__file__).parent.parent.parent / "scripts" / "readme" / "prompt_update.md"
