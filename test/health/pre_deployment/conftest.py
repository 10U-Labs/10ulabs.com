import importlib.util
import json
from pathlib import Path
from typing import Any, Dict
from types import ModuleType
from unittest.mock import Mock
import pytest


def parse_response_body(response: Dict[str, Any]) -> Any:
    return json.loads(response['body'])


def assert_response_status(response: Dict[str, Any], expected_code: int) -> None:
    assert response['statusCode'] == expected_code


def assert_json_content_type(response: Dict[str, Any]) -> None:
    assert response['headers']['Content-Type'].startswith('application/json')


def assert_cors_headers(response: Dict[str, Any]) -> None:
    assert 'Access-Control-Allow-Origin' in response['headers']


def load_health_handler_module() -> ModuleType:
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "health" / "health.py"
    spec = importlib.util.spec_from_file_location("health_handler", handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def health_handler() -> ModuleType:
    return load_health_handler_module()


@pytest.fixture
def lambda_context():
    return Mock()


@pytest.fixture
def health_get_event():
    return {'path': '/health', 'httpMethod': 'GET'}
