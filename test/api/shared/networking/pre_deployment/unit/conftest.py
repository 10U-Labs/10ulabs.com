"""Pytest fixtures for api/shared/networking pre-deployment unit tests."""

import pytest
from repo_utils import REPO_ROOT

API_SHARED_NETWORKING_DIR = REPO_ROOT / "src" / "api" / "shared" / "networking"
SHARED_MODULE_DIR = REPO_ROOT / "lib" / "terraform" / "modules" / "shared"


@pytest.fixture(name="api_shared_networking_dir")
def api_shared_networking_dir_fixture():
    """Provide path to api/shared/networking directory."""
    return API_SHARED_NETWORKING_DIR


@pytest.fixture(name="shared_module_dir")
def shared_module_dir_fixture():
    """Provide path to shared terraform module (single source of truth)."""
    return SHARED_MODULE_DIR
