"""Pytest fixtures for simulation-soc pre-deployment unit tests."""
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Dict
from unittest.mock import Mock

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
SIMULATION_SOC_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "simulation_soc"


def parse_response_body(response: Dict[str, Any]) -> Any:
    """Parse JSON body from Lambda response."""
    return json.loads(response['body'])


def assert_response_status(response: Dict[str, Any], expected_code: int) -> None:
    """Assert the response has the expected HTTP status code."""
    assert response['statusCode'] == expected_code


def assert_json_content_type(response: Dict[str, Any]) -> None:
    """Assert the response has JSON content type header."""
    assert response['headers']['Content-Type'].startswith('application/json')


def assert_cors_headers(response: Dict[str, Any]) -> None:
    """Assert the response has CORS headers."""
    assert 'Access-Control-Allow-Origin' in response['headers']


def load_simulation_soc_handler_module() -> ModuleType:
    """Load the simulation-soc handler module dynamically."""
    handler_path = SIMULATION_SOC_SRC / "lambda" / "handler.py"
    spec = importlib.util.spec_from_file_location("simulation_soc_handler", handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def simulation_soc_handler() -> ModuleType:
    """Provide the loaded simulation-soc handler module."""
    return load_simulation_soc_handler_module()


@pytest.fixture
def lambda_context():
    """Provide a mock Lambda context object."""
    return Mock()


@pytest.fixture
def simulation_soc_post_event_factory():
    """Provide a factory for creating simulation-soc POST events."""
    def _create_event(body_data=None, content_type='application/json'):
        if body_data is None:
            body_data = {'persona': 'riscv'}
        return {
            'path': '/v1/simulation-soc',
            'httpMethod': 'POST',
            'body': json.dumps(body_data),
            'headers': {'Content-Type': content_type, 'x-test-mode': 'true'},
            'requestContext': {'requestId': 'test-request-id'}
        }
    return _create_event
