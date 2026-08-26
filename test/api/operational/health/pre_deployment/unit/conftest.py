from pathlib import Path
from types import ModuleType

from test.api.operational.health.conftest import HEALTH_SRC

import pytest

from module_utils import create_lambda_loader


def load_health_handler_module() -> ModuleType:
    loader = create_lambda_loader(HEALTH_SRC / "lambda")
    return loader("handler.py", "health_handler")


@pytest.fixture
def health_handler() -> ModuleType:
    return load_health_handler_module()


@pytest.fixture
def health_get_event():
    return {'path': '/health', 'httpMethod': 'GET'}


@pytest.fixture
def health_src_dir() -> Path:
    return HEALTH_SRC
