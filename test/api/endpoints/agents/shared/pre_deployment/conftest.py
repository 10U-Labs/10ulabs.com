"""Pytest fixtures for agents/shared pre-deployment tests."""
import pytest

from terraform_config import REPO_ROOT

AGENTS_SHARED_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "agents" / "shared"
SHARED_MODULE_DIR = REPO_ROOT / "lib" / "terraform" / "modules" / "shared"


@pytest.fixture(name="agents_shared_dir")
def agents_shared_dir_fixture():
    """Provide path to agents/shared directory."""
    return AGENTS_SHARED_DIR


@pytest.fixture(name="shared_module_dir")
def shared_module_dir_fixture():
    """Provide path to shared terraform module (single source of truth)."""
    return SHARED_MODULE_DIR
