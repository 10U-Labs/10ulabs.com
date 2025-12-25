"""Pytest fixtures for hook tests."""
import sys
from types import ModuleType

import pytest
from module_utils import load_module_from_path
from repo_utils import REPO_ROOT

HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"

# Add hooks directory to path for imports
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


def load_hook_module(hook_name: str, module_name: str) -> ModuleType:
    """Load a hook module by name for testing."""
    hook_path = HOOKS_DIR / hook_name
    return load_module_from_path(module_name, hook_path)


@pytest.fixture
def pre_git_checks():
    """Load the pre_git_checks hook module."""
    return load_hook_module("pre_git_checks.py", "pre_git_checks")


@pytest.fixture
def bash_command_blocker():
    """Load the bash_command_blocker hook module."""
    return load_hook_module("bash_command_blocker.py", "bash_command_blocker")


@pytest.fixture
def file_creation_blocker():
    """Load the file_creation_blocker hook module."""
    return load_hook_module("file_creation_blocker.py", "file_creation_blocker")


@pytest.fixture
def lint_disable_blocker():
    """Load the lint_disable_blocker hook module."""
    return load_hook_module("lint_disable_blocker.py", "lint_disable_blocker")


@pytest.fixture
def s3_versioning_checker():
    """Load the s3_versioning_checker hook module."""
    return load_hook_module("s3_versioning_checker.py", "s3_versioning_checker")


@pytest.fixture
def code_quality_checker():
    """Load the code_quality_checker hook module."""
    return load_hook_module("code_quality_checker.py", "code_quality_checker")


@pytest.fixture
def test_standards_checker():
    """Load the test_standards_checker hook module."""
    return load_hook_module("test_standards_checker.py", "test_standards_checker")
