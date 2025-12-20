"""Pytest fixtures for pre-deployment unit tests."""

import pytest
from repo_utils import REPO_ROOT


SRC_DIR = REPO_ROOT / "src" / "www" / "shared"


@pytest.fixture
def src_dir():
    """Provide the source directory path."""
    return SRC_DIR
