"""Shared fixtures for retries pre-deployment tests."""
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT


RETRIES_SRC_PATH = (
    REPO_ROOT / "src" / "api" / "endpoints" / "github_workflows" / "retries"
)


@pytest.fixture
def retries_src_path() -> Path:
    """Provide path to retries source directory."""
    return RETRIES_SRC_PATH


@pytest.fixture
def terraform_dir() -> Path:
    """Provide path to retries terraform directory."""
    return RETRIES_SRC_PATH
