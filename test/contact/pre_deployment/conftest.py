import importlib.util
import json
from types import ModuleType
from typing import Any, Dict
from unittest.mock import Mock

from test.contact.conftest import CONTACT_SRC

import pytest


def parse_response_body(response: Dict[str, Any]) -> Any:
    return json.loads(response['body'])


def assert_response_status(response: Dict[str, Any], expected_code: int) -> None:
    assert response['statusCode'] == expected_code


def assert_json_content_type(response: Dict[str, Any]) -> None:
    assert response['headers']['Content-Type'].startswith('application/json')


def assert_cors_headers(response: Dict[str, Any]) -> None:
    assert 'Access-Control-Allow-Origin' in response['headers']


def load_contact_handler_module() -> ModuleType:
    handler_path = CONTACT_SRC / "lambda" / "handler.py"
    spec = importlib.util.spec_from_file_location("contact_handler", handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def contact_handler() -> ModuleType:
    return load_contact_handler_module()


@pytest.fixture
def lambda_context():
    return Mock()


@pytest.fixture
def contact_post_event():
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
