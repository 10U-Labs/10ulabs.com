"""Shared fixtures for ECS task stops pre-deployment unit tests."""
import sys
from pathlib import Path
from typing import Dict
from unittest.mock import Mock, patch

import pytest

from module_utils import create_lambda_loader
from repo_utils import REPO_ROOT


ECS_TASK_STOPS_SRC_PATH = (
    REPO_ROOT / "src" / "api" / "endpoints" / "ecs_task_stops"
)
ECS_TASK_STOPS_LAMBDA_PATH = ECS_TASK_STOPS_SRC_PATH / "lambda"

# Add lambda path to sys.path so modules can be found when patching
if str(ECS_TASK_STOPS_LAMBDA_PATH) not in sys.path:
    sys.path.insert(0, str(ECS_TASK_STOPS_LAMBDA_PATH))


def get_lambda_path(filename: str) -> Path:
    """Get the full path to a lambda file."""
    return ECS_TASK_STOPS_LAMBDA_PATH / filename


@pytest.fixture
def ecs_task_stops_src_path() -> Path:
    """Provide path to ecs_task_stops source directory."""
    return ECS_TASK_STOPS_SRC_PATH


# Use shared lambda loader for ecs_task_stops lambda
load_lambda_module = create_lambda_loader(ECS_TASK_STOPS_LAMBDA_PATH)


@pytest.fixture
def config(shared_config) -> Dict[str, str]:
    """Provide config for unit tests."""
    return {
        'aws_region': shared_config['aws_region'],
        'resource_prefix': shared_config['resource_prefix'],
    }


@pytest.fixture
def lambda_context():
    """Provide a mock Lambda context object."""
    return Mock()


@pytest.fixture
def handler_module(config):
    """Provide the handler module with mocked environment."""
    env_vars = {
        'AWS_REGION': config['aws_region'],
        'RETRIES_QUEUE_URL': 'https://sqs.us-east-2.amazonaws.com/123456789012/test-queue',
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("handler.py", "handler")
        yield module
