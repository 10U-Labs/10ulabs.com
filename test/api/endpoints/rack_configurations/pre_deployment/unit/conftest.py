from types import ModuleType

import pytest
from module_utils import create_lambda_loader
from test_fixtures.unit import reset_module_state
from repo_utils import REPO_ROOT

RACK_CONFIGURATIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "rack_configurations"
RACK_CONFIGURATIONS_LAMBDA_PATH = RACK_CONFIGURATIONS_SRC_PATH / "lambda"

load_lambda_module = create_lambda_loader(RACK_CONFIGURATIONS_LAMBDA_PATH)


@pytest.fixture
def handler() -> ModuleType:
    module = load_lambda_module("handler.py", "handler")
    reset_module_state(module, _clients={})
    return module
