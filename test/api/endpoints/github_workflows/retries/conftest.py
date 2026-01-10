"""Shared fixtures for github workflows retries endpoint tests."""
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT


RETRIES_SRC_PATH = (
    REPO_ROOT / "src" / "api" / "endpoints" / "github_workflows" / "retries"
)
RETRIES_LAMBDA_PATH = RETRIES_SRC_PATH / "lambda"


@pytest.fixture
def retries_src_path() -> Path:
    """Provide path to retries source directory."""
    return RETRIES_SRC_PATH


@pytest.fixture
def retries_lambda_path() -> Path:
    """Provide path to retries lambda directory."""
    return RETRIES_LAMBDA_PATH
