"""Shared fixtures for ECS task stops pre-deployment tests."""
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT


ECS_TASK_STOPS_SRC_PATH = (
    REPO_ROOT / "src" / "api" / "endpoints" / "ecs_task_stops"
)


@pytest.fixture
def ecs_task_stops_src_path() -> Path:
    """Provide path to ecs_task_stops source directory."""
    return ECS_TASK_STOPS_SRC_PATH


@pytest.fixture
def terraform_dir() -> Path:
    """Provide path to ecs_task_stops terraform directory."""
    return ECS_TASK_STOPS_SRC_PATH
