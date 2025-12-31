"""Shared fixtures and utilities for ECS runner pre-deployment unit tests."""
import sys
from types import ModuleType
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest

from lambda_response import (
    parse_response_body,
    assert_response_status,
    assert_json_content_type,
)
from urllib_mocks import create_mock_urllib_response
from module_utils import load_module_from_path, reset_module_state
from event_factories import create_ecs_runner_post_event
from aws_clients import reset_clients
from github_runner_api import reset_github_token_cache
from infra_validation import set_dependencies_status

from ...conftest import ECS_RUNNER_SRC

# Re-export for backward compatibility
__all__ = [
    'parse_response_body',
    'assert_response_status',
    'assert_json_content_type',
]


def load_handler_module() -> ModuleType:
    """Load the ECS runner handler module with its dependencies."""
    lambda_dir = ECS_RUNNER_SRC / "lambda"
    lambda_dir_str = str(lambda_dir)

    # Add lambda dir to path for local imports (clients, responses, etc.)
    if lambda_dir_str not in sys.path:
        sys.path.insert(0, lambda_dir_str)

    handler_path = lambda_dir / "handler.py"
    return load_module_from_path("ecs_runner_handler", handler_path)


@pytest.fixture
def ecs_runner_handler(config: Dict[str, str]) -> Any:
    """Provide the ECS runner handler module with mocked environment."""
    env_vars = {
        'AWS_REGION': config['aws_region'],
        'ECR_REPOSITORY': config['ecr_repository_name'],
        'GITHUB_REPO': config['github_repo'],
        'GITHUB_TOKEN_SECRET_NAME': config['ssm_parameter_name_for_github_pat'],
        'ECS_CLUSTER': config['cluster_name'],
        'CONTAINER_NAME': config['container_name'],
        'TASK_DEFINITION': config['task_family'],
        'API_FQDN': config['api_fqdn'],
        'SUBNETS': 'subnet-test1,subnet-test2',
        'SECURITY_GROUPS': 'sg-test',
        'VPC_ID': 'vpc-test'
    }
    with patch.dict('os.environ', env_vars):
        module = load_handler_module()
        reset_module_state(module)
        set_dependencies_status(checked=True, valid=True, errors=[])
        reset_clients()
        reset_github_token_cache()
        yield module
        reset_clients()
        reset_github_token_cache()


@pytest.fixture
def ecs_runner_post_event_factory():
    """Factory to create ECS runner POST event payloads."""
    return create_ecs_runner_post_event


@pytest.fixture
def mock_urllib_response_factory():
    """Factory to create mock urllib response objects."""
    return create_mock_urllib_response


@pytest.fixture
def lambda_context():
    """Provide a mock Lambda context object."""
    return Mock()


def create_mock_client_factory(ecs_mock=None, ssm_mock=None, ecr_mock=None):
    """Create a mock boto3 client factory function."""
    def mock_client(service_name):
        if service_name == 'ecs' and ecs_mock is not None:
            return ecs_mock
        if service_name == 'ssm' and ssm_mock is not None:
            return ssm_mock
        if service_name == 'ecr' and ecr_mock is not None:
            return ecr_mock
        return MagicMock()
    return mock_client


def create_fargate_runner_env(use_spot=None):
    """Create standard environment dict for fargate runner tests."""
    env = {
        'ECS_CLUSTER': 'test-cluster',
        'TASK_DEFINITION': 'test-task',
        'SUBNETS': 'subnet-1',
        'SECURITY_GROUPS': 'sg-1',
        'VPC_ID': 'vpc-test',
        'CONTAINER_NAME': 'test-container',
        'GITHUB_TOKEN_SECRET_NAME': '/test/token'
    }
    if use_spot is not None:
        env['USE_SPOT'] = 'true' if use_spot else 'false'
    return env


def create_mock_ssm_with_token(token_value='test-token'):
    """Create a mock SSM client that returns the given token."""
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': token_value}}
    return mock_ssm


def create_mock_ecs_with_run_task(task_arn='test-arn'):
    """Create a mock ECS client that returns success from run_task."""
    mock_ecs = MagicMock()
    mock_ecs.run_task.return_value = {'tasks': [{'taskArn': task_arn}]}
    return mock_ecs


def create_mock_ecs_for_status(task_arns=None):
    """Create a mock ECS client for status checks."""
    mock_ecs = MagicMock()
    mock_ecs.list_tasks.return_value = {'taskArns': task_arns or []}
    return mock_ecs
