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
