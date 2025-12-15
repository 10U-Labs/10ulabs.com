"""Pytest fixtures for agents pre-deployment unit tests."""
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from lambda_response import (
    parse_response_body,
    assert_response_status,
    assert_json_content_type,
    assert_cors_headers,
)

# Re-export for backward compatibility
__all__ = [
    "parse_response_body",
    "assert_response_status",
    "assert_json_content_type",
    "assert_cors_headers",
]

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


def _mock_github_auth() -> MagicMock:
    """Create mock for github_auth Lambda layer."""
    mock = MagicMock()
    mock.get_github_token = MagicMock(return_value="mock_github_token")
    return mock


def load_handler_module() -> ModuleType:
    """Load the agents handler module dynamically.

    Mocks the github_auth Lambda layer before importing.
    """
    # Mock the Lambda layer
    mock_github_auth = _mock_github_auth()
    sys.modules["github_auth"] = mock_github_auth

    handler_path = AGENTS_SRC / "lambdas" / "handler.py"
    spec = importlib.util.spec_from_file_location("agents_handler", handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def agents_handler() -> ModuleType:
    """Load and return the agents handler module."""
    return load_handler_module()


@pytest.fixture
def mock_github_auth() -> MagicMock:
    """Return a mock github_auth module."""
    return _mock_github_auth()
