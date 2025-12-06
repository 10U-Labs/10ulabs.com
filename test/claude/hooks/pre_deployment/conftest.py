"""Pytest fixtures for hook tests."""
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"

# Add hooks directory to path for imports
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


def load_hook_module(hook_name: str, module_name: str) -> ModuleType:
    """Load a hook module by name for testing."""
    hook_path = HOOKS_DIR / hook_name
    spec = importlib.util.spec_from_file_location(module_name, hook_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


@pytest.fixture
def sample_workflow():
    """Provide a sample workflow dictionary for testing."""
    return {
        'on': {
            'push': {
                'paths': ['src/**/*.py', 'test/**']
            }
        },
        'jobs': {
            'static-analysis': {
                'steps': [
                    {'name': 'Run pylint', 'run': 'pylint src/'},
                    {'name': 'Run mypy', 'run': 'mypy src/'},
                    {'name': 'Deploy', 'run': 'deploy.sh'}
                ]
            },
            'unit-tests': {
                'steps': [
                    {'name': 'Run unit tests', 'run': 'pytest test/pre_deployment/unit/'},
                    {'name': 'Coverage', 'run': 'coverage report'}
                ]
            }
        }
    }


@pytest.fixture
def sample_workflow_no_paths():
    """Provide a sample workflow without paths for testing."""
    return {
        'on': {
            'push': {}
        },
        'jobs': {}
    }
