"""Pytest fixtures for agents pre-deployment unit tests."""
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

try:
    from lambda_response import (
        parse_response_body,
        assert_response_status,
        assert_json_content_type,
        assert_cors_headers,
    )
except ImportError:
    # Stubs when lambda_response module is not available
    import json
    from typing import Any, Dict

    def parse_response_body(response: Dict[str, Any]) -> Any:
        """Parse JSON body from Lambda response."""
        return json.loads(response["body"])

    def assert_response_status(response: Dict[str, Any], expected_code: int) -> None:
        """Assert that response has expected HTTP status code."""
        assert response["statusCode"] == expected_code

    def assert_json_content_type(response: Dict[str, Any]) -> None:
        """Assert that response has JSON content type header."""
        assert response["headers"]["Content-Type"].startswith("application/json")

    def assert_cors_headers(response: Dict[str, Any]) -> None:
        """Assert that response includes CORS headers."""
        assert "Access-Control-Allow-Origin" in response["headers"]


# Re-export for backward compatibility
__all__ = [
    "parse_response_body",
    "assert_response_status",
    "assert_json_content_type",
    "assert_cors_headers",
]

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


def _create_mock_github_auth() -> MagicMock:
    """Create mock for github_auth Lambda layer."""
    mock = MagicMock()
    mock.get_github_token = MagicMock(return_value="mock_github_token")
    return mock


def _load_lambda_module(filename: str, module_name: str) -> ModuleType:
    """Load a Lambda handler module dynamically.

    Mocks the github_auth Lambda layer before importing.
    """
    github_auth_mock = _create_mock_github_auth()
    sys.modules["github_auth"] = github_auth_mock

    handler_path = AGENTS_SRC / "lambdas" / filename
    spec = importlib.util.spec_from_file_location(module_name, handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def webhook_handler() -> ModuleType:
    """Load and return the webhook handler module."""
    return _load_lambda_module("webhook.py", "webhook_handler")


@pytest.fixture
def scanner_handler() -> ModuleType:
    """Load and return the scanner handler module."""
    return _load_lambda_module("scanner.py", "scanner_handler")


@pytest.fixture
def invoker_handler() -> ModuleType:
    """Load and return the invoker handler module."""
    return _load_lambda_module("invoker.py", "invoker_handler")


@pytest.fixture
def mock_github_auth() -> MagicMock:
    """Return a mock github_auth module."""
    return _create_mock_github_auth()
