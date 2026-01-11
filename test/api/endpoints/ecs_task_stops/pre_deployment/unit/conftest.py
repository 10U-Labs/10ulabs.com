"""Shared fixtures for ECS task stops pre-deployment unit tests."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from module_utils import create_lambda_loader
from repo_utils import REPO_ROOT


ECS_ENDPOINT_NAME = "ecs_task_stops"
ECS_TASK_STOPS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / ECS_ENDPOINT_NAME
ECS_TASK_STOPS_LAMBDA = ECS_TASK_STOPS_SRC / "lambda"

if str(ECS_TASK_STOPS_LAMBDA) not in sys.path:
    sys.path.insert(0, str(ECS_TASK_STOPS_LAMBDA))

load_ecs_lambda_module = create_lambda_loader(ECS_TASK_STOPS_LAMBDA)


@pytest.fixture
def ecs_task_stops_src_path() -> Path:
    """Provide path to ecs_task_stops source directory."""
    return ECS_TASK_STOPS_SRC


@pytest.fixture
def handler_module(request):
    """Load the ECS task stops handler with mocked environment."""
    cfg = request.getfixturevalue('cfg')
    env = {
        'AWS_REGION': cfg['aws_region'],
        'RETRIES_QUEUE_URL': 'https://sqs.us-east-2.amazonaws.com/123456789012/test-queue',
    }
    with patch.dict('os.environ', env):
        yield load_ecs_lambda_module("handler.py", "handler")
