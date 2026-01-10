"""Shared fixtures for runners cleanup tests."""
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT


CLEANUPS_SRC_PATH = (
    REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "cleanups"
)
CLEANUPS_LAMBDA_PATH = CLEANUPS_SRC_PATH / "lambda"


@pytest.fixture
def cleanups_src_path() -> Path:
    """Provide path to cleanups source directory."""
    return CLEANUPS_SRC_PATH


@pytest.fixture
def cleanups_lambda_path() -> Path:
    """Provide path to cleanups lambda directory."""
    return CLEANUPS_LAMBDA_PATH
