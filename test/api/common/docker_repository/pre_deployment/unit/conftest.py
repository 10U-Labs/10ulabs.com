"""Pytest fixtures for api/common/docker_repository pre-deployment unit tests."""

import pytest
from repo_utils import REPO_ROOT

API_SHARED_DOCKER_REPOSITORY_DIR = REPO_ROOT / "src" / "api" / "shared" / "docker_repository"
SHARED_MODULE_DIR = REPO_ROOT / "lib" / "terraform" / "modules" / "shared"


@pytest.fixture(name="api_common_docker_repository_dir")
def api_common_docker_repository_dir_fixture():
    """Provide path to api/common/docker_repository directory."""
    return API_SHARED_DOCKER_REPOSITORY_DIR


@pytest.fixture(name="shared_module_dir")
def shared_module_dir_fixture():
    """Provide path to shared terraform module (single source of truth)."""
    return SHARED_MODULE_DIR
