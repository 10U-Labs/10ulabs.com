"""Pytest fixtures for api/shared/ecs_runner pre-deployment unit tests."""

import pytest
from repo_utils import REPO_ROOT

API_SHARED_ECS_RUNNER_DIR = REPO_ROOT / "src" / "api" / "shared" / "ecs_runner"
SHARED_MODULE_DIR = REPO_ROOT / "lib" / "terraform" / "modules" / "shared"


@pytest.fixture(name="api_shared_ecs_runner_dir")
def api_shared_ecs_runner_dir_fixture():
    """Provide path to api/shared/ecs_runner directory."""
    return API_SHARED_ECS_RUNNER_DIR


@pytest.fixture(name="shared_module_dir")
def shared_module_dir_fixture():
    """Provide path to shared terraform module (single source of truth)."""
    return SHARED_MODULE_DIR
