import json
from pathlib import Path
from types import ModuleType
from typing import Any, Dict

import pytest

from module_utils import create_lambda_loader
from repo_utils import REPO_ROOT

BACKEND_LAMBDA_PATH = REPO_ROOT / "src" / "api" / "common" / "routing" / "lambda"

load_lambda_module = create_lambda_loader(BACKEND_LAMBDA_PATH)


@pytest.fixture
def openapi_spec() -> Dict[str, Any]:
    base = Path(__file__).parent.parent.parent.parent.parent.parent.parent
    openapi_path = base / "src" / "www" / "api" / "openapi.json"
    with open(openapi_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def catchall_handler() -> ModuleType:
    return load_lambda_module("handler.py", "catchall_handler")


@pytest.fixture
def catchall_unknown_event() -> Dict[str, Any]:
    return {'path': '/unknown', 'httpMethod': 'GET'}
