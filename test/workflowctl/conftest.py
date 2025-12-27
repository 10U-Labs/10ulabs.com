"""Pytest configuration for workflowctl tests."""

import importlib.util
import sys

import pytest

from repo_utils import REPO_ROOT

WORKFLOWCTL_DIR = REPO_ROOT / "src" / "workflowctl"
sys.path.insert(0, str(WORKFLOWCTL_DIR))


def _load_module(name: str):
    """Load a module from the workflowctl directory."""
    module_path = WORKFLOWCTL_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {name} module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Load all workflowctl modules
_workflowctl_module = _load_module("workflowctl")
_utils_module = _load_module("utils")
_cancel_module = _load_module("cancel")
_dispatch_module = _load_module("dispatch")
_dispatch_roots_module = _load_module("dispatch_roots")
_get_changed_files_module = _load_module("get_changed_files")
_get_running_module = _load_module("get_running")
_compute_roots_module = _load_module("compute_roots")


@pytest.fixture
def workflowctl():
    """Provide access to the workflowctl module."""
    return _workflowctl_module


@pytest.fixture
def utils():
    """Provide access to the utils module."""
    return _utils_module


@pytest.fixture
def cancel():
    """Provide access to the cancel module."""
    return _cancel_module


@pytest.fixture
def dispatch():
    """Provide access to the dispatch module."""
    return _dispatch_module


@pytest.fixture
def dispatch_roots():
    """Provide access to the dispatch_roots module."""
    return _dispatch_roots_module


@pytest.fixture
def get_changed_files():
    """Provide access to the get_changed_files module."""
    return _get_changed_files_module


@pytest.fixture
def get_running():
    """Provide access to the get_running module."""
    return _get_running_module


@pytest.fixture
def compute_roots():
    """Provide access to the compute_roots module."""
    return _compute_roots_module
