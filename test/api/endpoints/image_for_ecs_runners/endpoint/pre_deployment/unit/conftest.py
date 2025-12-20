"""Fixtures for image_for_ecs_runners endpoint unit tests."""
import importlib.util
import sys
from unittest.mock import MagicMock

import pytest
from repo_utils import REPO_ROOT

LAMBDA_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "image_for_ecs_runners" / "lambda"
HANDLER_PATH = LAMBDA_DIR / "handler.py"

# Load the handler module
handler_spec = importlib.util.spec_from_file_location("handler", HANDLER_PATH)
if handler_spec is None or handler_spec.loader is None:
    raise ImportError("Could not load handler module")
handler = importlib.util.module_from_spec(handler_spec)
sys.modules['handler'] = handler
handler_spec.loader.exec_module(handler)


@pytest.fixture(autouse=True)
def reset_handler_state():
    """Reset handler module state before each test."""
    handler.set_test_mode(False)
    handler.set_client('ecr', None)
    yield
    handler.set_test_mode(False)
    handler.set_client('ecr', None)


@pytest.fixture
def mock_ecr_client():
    """Create a mock ECR client."""
    return MagicMock()


@pytest.fixture
def mock_ssm_client():
    """Create a mock SSM client."""
    return MagicMock()


@pytest.fixture
def sample_event():
    """Create a sample API Gateway event."""
    return {
        'httpMethod': 'GET',
        'path': '/v1/image-for-ecs-runners',
        'headers': {},
        'body': None,
        'pathParameters': None
    }


@pytest.fixture
def sample_event_with_test_mode():
    """Create a sample API Gateway event with test mode header."""
    return {
        'httpMethod': 'GET',
        'path': '/v1/image-for-ecs-runners',
        'headers': {'x-test-mode': 'true'},
        'body': None,
        'pathParameters': None
    }
