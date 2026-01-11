"""Shared fixtures for runners cleanup pre-deployment unit tests."""
from unittest.mock import patch

import pytest

from test_utils import create_endpoint_handler_loader


ENDPOINT_PATH = "runners/cleanups"
load_lambda_module = create_endpoint_handler_loader(ENDPOINT_PATH)


@pytest.fixture
def handler_module(cfg):
    """Provide the handler module with mocked environment."""
    env_vars = {
        'AWS_REGION': cfg['aws_region'],
        'GITHUB_TOKEN_SECRET_NAME': '/test/github/pat',
        'GITHUB_REPO': 'org/repo',
        'ECS_CLUSTER': 'arn:aws:ecs:us-east-2:123456789012:cluster/test-cluster',
        'EC2_MANAGED_BY_TAG': 'ec2-runner-api',
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("handler.py", "handler")
        yield module
