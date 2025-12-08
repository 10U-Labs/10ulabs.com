"""Pytest fixtures for pre-deployment unit tests."""
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
SRC_DIR = REPO_ROOT / "src" / "www" / "shared"


@pytest.fixture
def src_dir():
    """Provide the source directory path."""
    return SRC_DIR
