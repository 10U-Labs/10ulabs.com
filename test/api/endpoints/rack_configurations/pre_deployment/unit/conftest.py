"""Pytest fixtures for rack configurations pre-deployment unit tests."""
import pytest
from module_utils import create_lambda_loader
from repo_utils import REPO_ROOT

RACK_CONFIGURATIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "rack_configurations"
RACK_CONFIGURATIONS_LAMBDAS_PATH = RACK_CONFIGURATIONS_SRC_PATH / "lambdas"

load_lambda_module = create_lambda_loader(RACK_CONFIGURATIONS_LAMBDAS_PATH)


@pytest.fixture(name="handler")
def handler_fixture():
    """Provide the handler Lambda module for tests."""
    module = load_lambda_module("handler.py", "handler")
    module.clear_clients()
    return module


@pytest.fixture(name="backup_tf_path")
def backup_tf_path_fixture():
    """Provide the path to the backup.tf file."""
    return RACK_CONFIGURATIONS_SRC_PATH / "backup.tf"


@pytest.fixture(name="backup_tf_content")
def backup_tf_content_fixture(backup_tf_path):
    """Provide the content of the backup.tf file."""
    with open(backup_tf_path, encoding="utf-8") as f:
        return f.read()
