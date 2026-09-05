import json
from types import ModuleType
from typing import Any, Callable, Dict

import pytest

from module_utils import create_lambda_loader
from repo_utils import REPO_ROOT

DIAGNOSTICS_SRC = REPO_ROOT / "src" / "api" / "operational" / "diagnostics"

_load_lambda = create_lambda_loader(DIAGNOSTICS_SRC / "lambda")


def load_diagnostics_handler_module() -> ModuleType:
    return _load_lambda("handler.py", "diagnostics_handler")


@pytest.fixture
def echo_handler() -> ModuleType:
    return load_diagnostics_handler_module()


@pytest.fixture
def echo_post_event_factory() -> Callable[..., Dict[str, Any]]:
    def _create_event(
        body_data: Any = None,
        is_base64_encoded: bool = False,
        content_type: str = 'application/json'
    ) -> Dict[str, Any]:
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
