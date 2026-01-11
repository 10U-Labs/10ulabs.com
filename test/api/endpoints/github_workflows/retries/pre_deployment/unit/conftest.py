"""Shared fixtures for retries pre-deployment unit tests."""
from unittest.mock import patch

import pytest

from test_utils import create_endpoint_handler_loader


ENDPOINT_PATH = "github_workflows/retries"
load_lambda_module = create_endpoint_handler_loader(ENDPOINT_PATH)


@pytest.fixture
def handler_module(cfg):
    """Provide the handler module with mocked environment."""
    env_vars = {
        'AWS_REGION': cfg['aws_region'],
        'GITHUB_TOKEN_SECRET_NAME': '/test/github/pat',
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("handler.py", "handler")
        yield module
