"""Pytest configuration for workflowctl tests.

This module provides fixtures for testing workflowctl scripts. It uses dynamic
module loading because src/workflowctl/*.py are standalone scripts without
__init__.py (they're executed directly, not imported as packages).

Note: workflowctl tests mock subprocess calls, not AWS SDK calls. For AWS-related
tests, use pytest_plugins = ['test_fixtures.unit'] or ['test_fixtures.aws'].
"""

import importlib.util
import sys
from typing import Any, Dict

import pytest

from repo_utils import REPO_ROOT


# Standard dependency graph for testing workflowctl functionality.
# This graph represents a linear dependency chain with paths for file matching.
# Use this fixture when testing functions that need a realistic workflow graph.
SAMPLE_GRAPH: Dict[str, Dict[str, Any]] = {
    "bootstrap": {
        "name": "Bootstrap",
        "depends_on": [],
        "paths": [".github/workflows/bootstrap.yml", "src/bootstrap/**"],
    },
    "www_shared": {
        "name": "WWW Shared",
        "depends_on": ["bootstrap"],
        "paths": [".github/workflows/www_shared.yml", "src/www/shared/**"],
    },
    "api_shared_routing": {
        "name": "API Shared Routing",
        "depends_on": ["www_shared"],
        "paths": [".github/workflows/api_shared_routing.yml", "src/api/shared/routing/**"],
    },
    "api_operational_health": {
        "name": "API Operational Health",
        "depends_on": ["api_shared_routing"],
        "paths": [
            ".github/workflows/api_operational_health.yml",
            "src/api/operational/health/**",
        ],
    },
}

# Extended dependency graph with deep linear chain for comprehensive testing.
# Use this for testing deep ancestor/descendant traversal algorithms.
EXTENDED_LINEAR_GRAPH: Dict[str, Dict[str, Any]] = {
    "bootstrap": {
        "name": "Bootstrap",
        "depends_on": [],
        "paths": [".github/workflows/bootstrap.yml", "src/bootstrap/**"],
    },
    "www_shared": {
        "name": "WWW Shared",
        "depends_on": ["bootstrap"],
        "paths": [".github/workflows/www_shared.yml", "src/www/shared/**"],
    },
    "api": {
        "name": "API",
        "depends_on": ["www_shared"],
        "paths": [".github/workflows/api_shared_routing.yml", "src/api/shared/routing/**"],
    },
    "health": {
        "name": "Health",
        "depends_on": ["api"],
        "paths": [
            ".github/workflows/api_operational_health.yml",
            "src/api/operational/health/**",
        ],
    },
    "ecr": {
        "name": "ECR",
        "depends_on": ["health"],
        "paths": [".github/workflows/api_shared_ecr.yml", "src/api/shared/ecr/**"],
    },
    "ecs_images": {
        "name": "Image for ECS Runners",
        "depends_on": ["ecr"],
        "paths": [
            ".github/workflows/api_endpoint_v1_runners_ecs_images.yml",
            "src/api/endpoints/runners/ecs/images/**",
        ],
    },
    "ecs_runner": {
        "name": "ECS Runner",
        "depends_on": ["ecs_images"],
        "paths": [
            ".github/workflows/api_endpoint_v1_runners_ecs.yml",
            "src/api/endpoints/runners/ecs/**",
        ],
    },
    "contact": {
        "name": "Contact",
        "depends_on": ["ecs_runner"],
        "paths": [
            ".github/workflows/api_endpoint_v1_contact.yml",
            "src/api/endpoints/contact/**",
        ],
    },
}

# Diamond-shaped dependency graph for testing multi-parent scenarios.
# www_app depends on both www_shared and api_shared (diamond pattern).
DIAMOND_GRAPH: Dict[str, Dict[str, Any]] = {
    "bootstrap": {"name": "Bootstrap", "depends_on": []},
    "www_shared": {"name": "WWW Shared", "depends_on": ["bootstrap"]},
    "api_shared": {"name": "API Shared", "depends_on": ["bootstrap"]},
    "www_app": {"name": "WWW App", "depends_on": ["www_shared", "api_shared"]},
}

# Minimal dependency graph for basic utility testing.
# Use this for simple tests that don't need complex graph structures.
MINIMAL_GRAPH: Dict[str, Dict[str, Any]] = {
    "bootstrap": {
        "name": "Ensuring bootstrap infrastructure exists and is properly configured",
        "depends_on": [],
        "paths": ["src/bootstrap/**"],
    },
    "www_shared": {
        "name": "WWW Shared",
        "depends_on": ["bootstrap"],
        "paths": ["src/www/shared/**"],
    },
    "api_shared_routing": {
        "name": "Ensuring API backend exists and is properly configured",
        "depends_on": ["www_shared"],
        "paths": ["src/api/backend/**"],
    },
}

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
_dispatch_descendants_module = _load_module("dispatch_descendants")
_dispatch_roots_module = _load_module("dispatch_roots")
_get_changed_files_module = _load_module("get_changed_files")
_get_running_module = _load_module("get_running")
_compute_roots_module = _load_module("compute_roots")
_dispatch_workflow_module = _load_module("dispatch_workflow")


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
def dispatch_descendants():
    """Provide access to the dispatch_descendants module."""
    return _dispatch_descendants_module


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


@pytest.fixture
def dispatch_workflow():
    """Provide access to the dispatch_workflow module."""
    return _dispatch_workflow_module


@pytest.fixture
def sample_graph() -> Dict[str, Dict[str, Any]]:
    """Provide a standard dependency graph for testing.

    This graph represents a linear chain:
    bootstrap -> www_shared -> api_shared_routing -> api_operational_health

    Each workflow has name, depends_on, and paths fields.
    """
    return SAMPLE_GRAPH.copy()


@pytest.fixture
def extended_linear_graph() -> Dict[str, Dict[str, Any]]:
    """Provide an extended linear dependency graph for testing.

    This graph represents a deep linear chain:
    bootstrap -> www_shared -> api -> health -> ecr -> ecs_images -> ecs_runner -> contact

    Use this for testing deep ancestor/descendant traversal algorithms.
    """
    return EXTENDED_LINEAR_GRAPH.copy()


@pytest.fixture
def diamond_graph() -> Dict[str, Dict[str, Any]]:
    """Provide a diamond-shaped dependency graph for testing.

    This graph has multiple paths to www_app:
    bootstrap -> www_shared -> www_app
    bootstrap -> api_shared -> www_app

    Use this for testing multi-parent dependency scenarios.
    """
    return DIAMOND_GRAPH.copy()


@pytest.fixture
def minimal_graph() -> Dict[str, Dict[str, Any]]:
    """Provide a minimal dependency graph for basic testing.

    This graph is a simple 3-node linear chain for utility tests.
    """
    return MINIMAL_GRAPH.copy()
