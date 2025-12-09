"""Pytest fixtures for api/shared/runners pre-deployment tests."""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
API_SHARED_RUNNERS_DIR = REPO_ROOT / "src" / "api" / "shared" / "runners"
SHARED_MODULE_DIR = REPO_ROOT / "lib" / "terraform" / "modules" / "shared"


@pytest.fixture(name="api_shared_runners_dir")
def api_shared_runners_dir_fixture():
    """Provide path to api/shared/runners directory."""
    return API_SHARED_RUNNERS_DIR


@pytest.fixture(name="shared_module_dir")
def shared_module_dir_fixture():
    """Provide path to shared terraform module (single source of truth)."""
    return SHARED_MODULE_DIR
