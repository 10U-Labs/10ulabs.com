import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent


def load_hook_module(hook_name: str, module_name: str) -> ModuleType:
    hook_path = REPO_ROOT / ".claude" / "hooks" / hook_name
    spec = importlib.util.spec_from_file_location(module_name, hook_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def pre_git_checks():
    return load_hook_module("pre_git_checks.py", "pre_git_checks")


@pytest.fixture
def bash_command_blocker():
    return load_hook_module("bash-command-blocker.py", "bash_command_blocker")


@pytest.fixture
def file_creation_blocker():
    return load_hook_module("file-creation-blocker.py", "file_creation_blocker")


@pytest.fixture
def lint_disable_blocker():
    return load_hook_module("lint-disable-blocker.py", "lint_disable_blocker")


@pytest.fixture
def s3_versioning_checker():
    return load_hook_module("s3-versioning-checker.py", "s3_versioning_checker")


@pytest.fixture
def code_quality_checker():
    return load_hook_module("code-quality-checker.py", "code_quality_checker")


@pytest.fixture
def test_standards_checker():
    return load_hook_module("test-standards-checker.py", "test_standards_checker")


@pytest.fixture
def sample_workflow():
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
                    {'name': 'Run pre_deployment tests', 'run': 'pytest test/pre_deployment/'},
                    {'name': 'Coverage', 'run': 'coverage report'}
                ]
            }
        }
    }


@pytest.fixture
def sample_workflow_no_paths():
    return {
        'on': {
            'push': {}
        },
        'jobs': {}
    }
