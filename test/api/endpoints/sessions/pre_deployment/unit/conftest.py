"""Pytest fixtures for sessions pre-deployment unit tests."""
import os
from unittest.mock import patch, MagicMock

import pytest
from module_utils import create_lambda_loader
from repo_utils import REPO_ROOT

SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"
SESSIONS_LAMBDA_PATH = SESSIONS_SRC_PATH / "lambda"
SESSIONS_LAMBDAS_PATH = SESSIONS_SRC_PATH / "lambdas"

load_lambda_module = create_lambda_loader(SESSIONS_LAMBDA_PATH)
load_analytics_module = create_lambda_loader(SESSIONS_LAMBDAS_PATH)


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
        module = load_analytics_module("crawler_trigger.py", "crawler_trigger")
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
        module = load_analytics_module("export_handler.py", "export_handler")
        yield module, mock_dynamodb_client
    del os.environ['DYNAMODB_TABLE_ARN']
    del os.environ['S3_BUCKET']
    del os.environ['S3_PREFIX']
