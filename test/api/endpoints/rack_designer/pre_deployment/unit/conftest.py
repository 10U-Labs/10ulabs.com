"""Pytest fixtures for rack designer pre-deployment unit tests."""
import importlib.util
import os
from types import ModuleType
from unittest.mock import patch, MagicMock

import pytest
from repo_utils import REPO_ROOT

RACK_DESIGNER_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "rack_designer"
RACK_DESIGNER_LAMBDAS_PATH = RACK_DESIGNER_SRC_PATH / "lambdas"


def load_lambda_module(filename: str, module_name: str) -> ModuleType:
    """Load a Lambda module from the rack designer lambdas directory."""
    handler_path = RACK_DESIGNER_LAMBDAS_PATH / filename
    spec = importlib.util.spec_from_file_location(module_name, handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="handler")
def handler_fixture():
    """Provide the handler Lambda module for tests."""
    module = load_lambda_module("handler.py", "handler")
    module.clear_clients()
    return module


@pytest.fixture(name="crawler_module")
def crawler_module_fixture():
    """Provide the crawler trigger Lambda module for tests."""
    os.environ['CRAWLER_NAME'] = 'test-crawler'
    with patch('boto3.client') as mock_client:
        mock_glue_client = MagicMock()
        mock_client.return_value = mock_glue_client
        module = load_lambda_module("crawler_trigger.py", "crawler_trigger")
        yield module, mock_glue_client
    del os.environ['CRAWLER_NAME']


@pytest.fixture(name="export_module")
def export_module_fixture():
    """Provide the export handler Lambda module for tests."""
    os.environ['DYNAMODB_TABLE_ARN'] = 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events'
    os.environ['S3_BUCKET'] = 'test-bucket'
    os.environ['S3_PREFIX'] = 'exports/events'
    with patch('boto3.client') as mock_client:
        mock_dynamodb_client = MagicMock()
        mock_client.return_value = mock_dynamodb_client
        module = load_lambda_module("export_handler.py", "export_handler")
        yield module, mock_dynamodb_client
    del os.environ['DYNAMODB_TABLE_ARN']
    del os.environ['S3_BUCKET']
    del os.environ['S3_PREFIX']


@pytest.fixture(name="backup_tf_path")
def backup_tf_path_fixture():
    """Provide the path to the backup.tf file."""
    return RACK_DESIGNER_SRC_PATH / "backup.tf"


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
