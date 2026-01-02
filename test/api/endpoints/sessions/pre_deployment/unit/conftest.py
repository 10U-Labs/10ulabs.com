"""Pytest fixtures for sessions pre-deployment unit tests."""
from unittest.mock import MagicMock

import pytest
from module_utils import create_lambda_loader
from repo_utils import REPO_ROOT

SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"
SESSIONS_LAMBDA_PATH = SESSIONS_SRC_PATH / "lambda"

load_lambda_module = create_lambda_loader(SESSIONS_LAMBDA_PATH)


@pytest.fixture(name="handler")
def handler_fixture():
    """Provide the handler Lambda module for tests."""
    module = load_lambda_module("handler.py", "handler")
    module.clear_clients()
    return module


def create_mock_dynamodb(method_name: str, return_value=None):
    """Create a mock DynamoDB client with a specified method returning a value.

    Args:
        method_name: The DynamoDB method to mock (e.g., 'batch_write_item').
        return_value: The value to return from the method. Defaults to {}.

    Returns:
        A mock DynamoDB client.
    """
    if return_value is None:
        return_value = {}
    mock_dynamodb = MagicMock()
    getattr(mock_dynamodb, method_name).return_value = return_value
    return mock_dynamodb
