import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Dict
from unittest.mock import Mock

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
ECHO_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "echo"


def parse_response_body(response: Dict[str, Any]) -> Any:
    return json.loads(response['body'])


def assert_response_status(response: Dict[str, Any], expected_code: int) -> None:
    assert response['statusCode'] == expected_code


def assert_json_content_type(response: Dict[str, Any]) -> None:
    assert response['headers']['Content-Type'].startswith('application/json')


def assert_cors_headers(response: Dict[str, Any]) -> None:
    assert 'Access-Control-Allow-Origin' in response['headers']


def load_echo_handler_module() -> ModuleType:
    handler_path = ECHO_SRC / "lambda" / "handler.py"
    spec = importlib.util.spec_from_file_location("echo_handler", handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def echo_handler() -> ModuleType:
    return load_echo_handler_module()


@pytest.fixture
def lambda_context():
    return Mock()


@pytest.fixture
def echo_post_event_factory():
    def _create_event(body_data=None, is_base64_encoded=False, content_type='application/json'):
        if body_data is None:
            body_data = {'test': 'data'}
        return {
            'path': '/v1/echo',
            'httpMethod': 'POST',
            'body': json.dumps(body_data) if not is_base64_encoded else body_data,
            'isBase64Encoded': is_base64_encoded,
            'headers': {'Content-Type': content_type},
            'requestContext': {'requestId': 'test-request-id'}
        }
    return _create_event
