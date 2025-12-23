"""Pytest fixtures for echo handler pre-deployment unit tests."""
import importlib.util
import json
from types import ModuleType

import pytest

from lambda_response import (
    parse_response_body,
    assert_response_status,
    assert_json_content_type,
    assert_cors_headers,
)
from repo_utils import REPO_ROOT

# Re-export for backward compatibility
__all__ = [
    'parse_response_body',
    'assert_response_status',
    'assert_json_content_type',
    'assert_cors_headers',
]

ECHO_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "echo"


def load_echo_handler_module() -> ModuleType:
    """Load the echo handler module dynamically."""
    handler_path = ECHO_SRC / "lambda" / "handler.py"
    spec = importlib.util.spec_from_file_location("echo_handler", handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def echo_handler() -> ModuleType:
    """Load and return the echo handler module."""
    return load_echo_handler_module()


@pytest.fixture
def echo_post_event_factory():
    """Factory fixture for creating echo POST event payloads."""
    def _create_event(body_data=None, is_base64_encoded=False, content_type='application/json'):
        if body_data is None:
            body_data = {'test': 'data'}
        return {
            'path': '/diagnostics/echo',
            'httpMethod': 'POST',
            'body': json.dumps(body_data) if not is_base64_encoded else body_data,
            'isBase64Encoded': is_base64_encoded,
            'headers': {'Content-Type': content_type},
            'requestContext': {'requestId': 'test-request-id'}
        }
    return _create_event
