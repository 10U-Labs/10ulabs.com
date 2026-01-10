"""Shared fixtures for runners cleanup pre-deployment unit tests."""
import sys
from pathlib import Path
from typing import Dict
from unittest.mock import Mock, patch

import pytest

from module_utils import create_lambda_loader
from repo_utils import REPO_ROOT


CLEANUPS_SRC_PATH = (
    REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "cleanups"
)
CLEANUPS_LAMBDA_PATH = CLEANUPS_SRC_PATH / "lambda"

# Add lambda path to sys.path so modules can be found when patching
if str(CLEANUPS_LAMBDA_PATH) not in sys.path:
    sys.path.insert(0, str(CLEANUPS_LAMBDA_PATH))


def get_lambda_path(filename: str) -> Path:
    """Get the full path to a lambda file."""
    return CLEANUPS_LAMBDA_PATH / filename


@pytest.fixture
def cleanups_src_path() -> Path:
    """Provide path to cleanups source directory."""
    return CLEANUPS_SRC_PATH


# Use shared lambda loader for cleanups lambda
load_lambda_module = create_lambda_loader(CLEANUPS_LAMBDA_PATH)


@pytest.fixture
def config(shared_config) -> Dict[str, str]:
    """Provide config for unit tests."""
    return {
        'aws_region': shared_config['aws_region'],
        'resource_prefix': shared_config['resource_prefix'],
    }


@pytest.fixture
def lambda_context():
    """Provide a mock Lambda context object."""
    return Mock()


@pytest.fixture
def handler_module(config):
    """Provide the handler module with mocked environment."""
    env_vars = {
        'AWS_REGION': config['aws_region'],
        'GITHUB_TOKEN_SECRET_NAME': '/test/github/pat',
        'GITHUB_REPO': 'org/repo',
        'ECS_CLUSTER': 'arn:aws:ecs:us-east-2:123456789012:cluster/test-cluster',
        'EC2_MANAGED_BY_TAG': 'ec2-runner-api',
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("handler.py", "handler")
        yield module
