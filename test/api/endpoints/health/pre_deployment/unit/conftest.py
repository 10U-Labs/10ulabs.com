"""Pytest fixtures for health endpoint pre-deployment tests."""
import importlib.util
import json
from types import ModuleType
from typing import Any, Dict
from unittest.mock import Mock

from test.api.endpoints.health.conftest import HEALTH_SRC

import pytest


def parse_response_body(response: Dict[str, Any]) -> Any:
    """Parse JSON response body from Lambda response."""
    return json.loads(response['body'])


def assert_response_status(response: Dict[str, Any], expected_code: int) -> None:
    """Assert that response has expected status code."""
    assert response['statusCode'] == expected_code


def assert_json_content_type(response: Dict[str, Any]) -> None:
    """Assert that response has JSON content type."""
    assert response['headers']['Content-Type'].startswith('application/json')


def assert_cors_headers(response: Dict[str, Any]) -> None:
    """Assert that response has CORS headers."""
    assert 'Access-Control-Allow-Origin' in response['headers']


def load_health_handler_module() -> ModuleType:
    """Load the health handler module dynamically."""
    handler_path = HEALTH_SRC / "lambda" / "handler.py"
    spec = importlib.util.spec_from_file_location("health_handler", handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def health_handler() -> ModuleType:
    """Create health handler module fixture."""
    return load_health_handler_module()


@pytest.fixture
def lambda_context():
    """Create mock Lambda context fixture."""
    return Mock()


@pytest.fixture
def health_get_event():
    """Create GET /health event fixture."""
    return {'path': '/health', 'httpMethod': 'GET'}


@pytest.fixture
def health_dependencies_get_event():
    """Create GET /health/dependencies event fixture."""
    return {'path': '/health/dependencies', 'httpMethod': 'GET'}
