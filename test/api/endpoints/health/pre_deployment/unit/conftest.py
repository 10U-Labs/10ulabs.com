"""Pytest fixtures for health endpoint pre-deployment tests."""
import importlib.util
from types import ModuleType

from test.api.endpoints.health.conftest import HEALTH_SRC

import pytest

from lambda_response import (
    parse_response_body,
    assert_response_status,
    assert_json_content_type,
    assert_cors_headers,
)

# Re-export for backward compatibility
__all__ = [
    'parse_response_body',
    'assert_response_status',
    'assert_json_content_type',
    'assert_cors_headers',
]


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
def health_get_event():
    """Create GET /health event fixture."""
    return {'path': '/health', 'httpMethod': 'GET'}


@pytest.fixture
def health_dependencies_get_event():
    """Create GET /health/dependencies event fixture."""
    return {'path': '/health/dependencies', 'httpMethod': 'GET'}
