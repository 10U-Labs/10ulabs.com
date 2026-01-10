"""Shared fixtures for ECS task stops tests."""
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT


ECS_TASK_STOPS_SRC_PATH = (
    REPO_ROOT / "src" / "api" / "endpoints" / "ecs_task_stops"
)
ECS_TASK_STOPS_LAMBDA_PATH = ECS_TASK_STOPS_SRC_PATH / "lambda"


@pytest.fixture
def ecs_task_stops_src_path() -> Path:
    """Provide path to ecs_task_stops source directory."""
    return ECS_TASK_STOPS_SRC_PATH


@pytest.fixture
def ecs_task_stops_lambda_path() -> Path:
    """Provide path to ecs_task_stops lambda directory."""
    return ECS_TASK_STOPS_LAMBDA_PATH
