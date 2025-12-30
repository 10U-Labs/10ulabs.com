"""Pytest fixtures for api/shared/parameters pre-deployment unit tests."""

import pytest
from repo_utils import REPO_ROOT

API_SHARED_PARAMETERS_DIR = REPO_ROOT / "src" / "api" / "shared" / "parameters"
SHARED_MODULE_DIR = REPO_ROOT / "lib" / "terraform" / "modules" / "shared"


@pytest.fixture(name="api_shared_parameters_dir")
def api_shared_parameters_dir_fixture():
    """Provide path to api/shared/parameters directory."""
    return API_SHARED_PARAMETERS_DIR


@pytest.fixture(name="shared_module_dir")
def shared_module_dir_fixture():
    """Provide path to shared terraform module (single source of truth)."""
    return SHARED_MODULE_DIR
