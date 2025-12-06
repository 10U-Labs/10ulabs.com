"""Pytest fixtures for contact handler pre-deployment tests."""
import importlib.util
import json
from types import ModuleType
from typing import Any, Dict
from unittest.mock import Mock

from test.api.endpoints.contact.conftest import CONTACT_SRC

import pytest


def parse_response_body(response: Dict[str, Any]) -> Any:
    """Parse JSON response body from Lambda response."""
    return json.loads(response['body'])


def assert_response_status(response: Dict[str, Any], expected_code: int) -> None:
    """Assert that response has expected HTTP status code."""
    assert response['statusCode'] == expected_code


def assert_json_content_type(response: Dict[str, Any]) -> None:
    """Assert that response has JSON content type header."""
    assert response['headers']['Content-Type'].startswith('application/json')


def assert_cors_headers(response: Dict[str, Any]) -> None:
    """Assert that response includes CORS headers."""
    assert 'Access-Control-Allow-Origin' in response['headers']


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
def lambda_context():
    """Create a mock Lambda context object."""
    return Mock()


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
