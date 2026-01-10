"""Shared fixtures for runners cleanup pre-deployment integration tests."""
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT


CLEANUPS_SRC_PATH = (
    REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "cleanups"
)


@pytest.fixture
def terraform_dir() -> Path:
    """Provide path to cleanups terraform directory."""
    return CLEANUPS_SRC_PATH
