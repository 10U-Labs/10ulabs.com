import pytest
from module_utils import create_lambda_loader
from repo_utils import REPO_ROOT

RACK_CONFIGURATIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "rack_configurations"
RACK_CONFIGURATIONS_LAMBDA_PATH = RACK_CONFIGURATIONS_SRC_PATH / "lambda"

load_lambda_module = create_lambda_loader(RACK_CONFIGURATIONS_LAMBDA_PATH)


@pytest.fixture
def handler():
    module = load_lambda_module("handler.py", "handler")
    module.clear_clients()
    return module
