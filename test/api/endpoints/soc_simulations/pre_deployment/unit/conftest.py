"""Pytest fixtures for simulation-soc pre-deployment unit tests."""
import json
from types import ModuleType

import pytest

from module_utils import load_module_from_path
from repo_utils import REPO_ROOT

SOC_SIMULATIONS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "soc_simulations"


def load_simulation_soc_handler_module() -> ModuleType:
    """Load the simulation-soc handler module dynamically."""
    handler_path = SOC_SIMULATIONS_SRC / "lambda" / "handler.py"
    return load_module_from_path("simulation_soc_handler", handler_path)


@pytest.fixture
def simulation_soc_handler() -> ModuleType:
    """Provide the loaded simulation-soc handler module."""
    return load_simulation_soc_handler_module()


@pytest.fixture
def simulation_soc_post_event_factory():
    """Provide a factory for creating simulation-soc POST events."""
    def _create_event(body_data=None, content_type='application/json'):
        if body_data is None:
            body_data = {'persona': 'riscv'}
        return {
            'path': '/v1/soc-simulations',
            'httpMethod': 'POST',
            'body': json.dumps(body_data),
            'headers': {'Content-Type': content_type, 'x-test-mode': 'true'},
            'requestContext': {'requestId': 'test-request-id'}
        }
    return _create_event
