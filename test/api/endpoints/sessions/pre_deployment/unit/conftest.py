"""Pytest fixtures for sessions pre-deployment unit tests."""
import os
from unittest.mock import patch, MagicMock

import pytest
from module_utils import create_lambda_loader
from repo_utils import REPO_ROOT

SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"
SESSIONS_TRACKER_PATH = SESSIONS_SRC_PATH / "lambda" / "tracker"
SESSIONS_EXPORTER_PATH = SESSIONS_SRC_PATH / "lambda" / "exporter"

load_lambda_module = create_lambda_loader(SESSIONS_TRACKER_PATH)
load_analytics_module = create_lambda_loader(SESSIONS_EXPORTER_PATH)


@pytest.fixture
def handler():
    """Provide the handler Lambda module for tests."""
    module = load_lambda_module("handler.py", "handler")
    module.clear_clients()
    return module


@pytest.fixture
def export_module():
    """Provide the export handler Lambda module for tests."""
    os.environ['DYNAMODB_TABLE_ARN'] = 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events'
    os.environ['S3_BUCKET'] = 'test-bucket'
    os.environ['S3_PREFIX'] = 'exports/events'
    with patch('boto3.client') as mock_client:
        mock_dynamodb_client = MagicMock()
        mock_client.return_value = mock_dynamodb_client
        module = load_analytics_module("handler.py", "export_handler")
        yield module, mock_dynamodb_client
    del os.environ['DYNAMODB_TABLE_ARN']
    del os.environ['S3_BUCKET']
    del os.environ['S3_PREFIX']
