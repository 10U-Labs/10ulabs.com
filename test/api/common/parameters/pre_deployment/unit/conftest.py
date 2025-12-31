"""Pytest fixtures for api/common/parameters pre-deployment unit tests."""

import pytest
from repo_utils import REPO_ROOT

API_SHARED_PARAMETERS_DIR = REPO_ROOT / "src" / "api" / "shared" / "parameters"
COMMON_MODULE_DIR = REPO_ROOT / "lib" / "terraform" / "common"


@pytest.fixture(name="api_common_parameters_dir")
def api_common_parameters_dir_fixture():
    """Provide path to api/common/parameters directory."""
    return API_SHARED_PARAMETERS_DIR


@pytest.fixture(name="shared_module_dir")
def shared_module_dir_fixture():
    """Provide path to shared terraform module (single source of truth)."""
    return COMMON_MODULE_DIR
