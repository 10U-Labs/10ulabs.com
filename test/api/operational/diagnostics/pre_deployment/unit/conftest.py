"""Pytest fixtures for diagnostics handler pre-deployment unit tests."""
import json
from types import ModuleType

import pytest

from module_utils import create_lambda_loader
from repo_utils import REPO_ROOT

DIAGNOSTICS_SRC = REPO_ROOT / "src" / "api" / "operational" / "diagnostics"

# Create loader for diagnostics lambda directory
_load_lambda = create_lambda_loader(DIAGNOSTICS_SRC / "lambda")


def load_diagnostics_handler_module() -> ModuleType:
    """Load the diagnostics handler module dynamically."""
    return _load_lambda("handler.py", "diagnostics_handler")


@pytest.fixture
def diagnostics_handler() -> ModuleType:
    """Load and return the diagnostics handler module."""
    return load_diagnostics_handler_module()


@pytest.fixture
def echo_handler() -> ModuleType:
    """Load and return the diagnostics handler module (alias for compatibility)."""
    return load_diagnostics_handler_module()


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
