"""Pytest fixtures for health endpoint pre-deployment tests."""
from pathlib import Path
from types import ModuleType

from test.api.operational.health.conftest import HEALTH_SRC

import pytest

from module_utils import create_lambda_loader


def load_health_handler_module() -> ModuleType:
    """Load the health handler module dynamically."""
    loader = create_lambda_loader(HEALTH_SRC / "lambda")
    return loader("handler.py", "health_handler")


@pytest.fixture
def health_handler() -> ModuleType:
    """Create health handler module fixture."""
    return load_health_handler_module()


@pytest.fixture
def health_get_event():
    """Create GET /health event fixture."""
    return {'path': '/health', 'httpMethod': 'GET'}


@pytest.fixture
def health_src_dir() -> Path:
    """Provide the health endpoint source directory path."""
    return HEALTH_SRC
