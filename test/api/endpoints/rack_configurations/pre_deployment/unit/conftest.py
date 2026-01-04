"""Pytest fixtures for rack configurations pre-deployment unit tests."""
from unittest.mock import MagicMock

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


def create_mock_dynamodb(method_name: str, return_value=None):
    """Create a mock DynamoDB client with a specified method returning a value.

    Args:
        method_name: The DynamoDB method to mock (e.g., 'put_item', 'get_item').
        return_value: The value to return from the method. Defaults to {}.

    Returns:
        A tuple of (mock_boto_client_patcher, mock_dynamodb_client).
    """
    if return_value is None:
        return_value = {}
    mock_dynamodb = MagicMock()
    getattr(mock_dynamodb, method_name).return_value = return_value
    return mock_dynamodb
