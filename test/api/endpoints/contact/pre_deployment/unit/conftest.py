"""Pytest fixtures for contact handler pre-deployment unit tests."""
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

CONTACT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "contact"


def load_contact_handler_module() -> ModuleType:
    """Load the contact handler module dynamically."""
    handler_path = CONTACT_SRC / "lambda" / "handler.py"
    spec = importlib.util.spec_from_file_location("contact_handler", handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def contact_handler() -> ModuleType:
    """Load and return the contact handler module."""
    return load_contact_handler_module()


@pytest.fixture
def contact_post_event():
    """Create a sample POST event for contact endpoint testing."""
    return {
        'path': '/v1/contact',
        'httpMethod': 'POST',
        'headers': {},
        'body': json.dumps({
            'name': 'John Doe',
            'email': 'john@example.com',
            'message': 'Hello, this is a test message.',
            'recaptcha_token': 'valid-token'
        }),
        'requestContext': {'requestId': 'test-id'}
    }
