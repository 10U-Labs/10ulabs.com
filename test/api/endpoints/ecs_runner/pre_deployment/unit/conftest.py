"""Shared fixtures and utilities for ECS runner pre-deployment unit tests."""
import importlib.util
import json
from types import ModuleType
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from lambda_response import (
    parse_response_body,
    assert_response_status,
    assert_json_content_type,
)
from urllib_mocks import create_mock_urllib_response

from ...conftest import ECS_RUNNER_SRC

# Re-export for backward compatibility
__all__ = [
    'parse_response_body',
    'assert_response_status',
    'assert_json_content_type',
]


def load_handler_module() -> ModuleType:
    """Load the ECS runner handler module dynamically."""
    handler_path = ECS_RUNNER_SRC / "lambda" / "handler.py"
    spec = importlib.util.spec_from_file_location("ecs_runner_handler", handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        'IMAGE_API_ENDPOINT': f"https://{config['api_fqdn']}/{config['api_version']}",
        'SUBNETS': 'subnet-test1,subnet-test2',
        'SECURITY_GROUPS': 'sg-test',
        'VPC_ID': 'vpc-test',
        'WORKFLOW_RUNNERS_TABLE': 'test-workflow-runners'
    }
    with patch.dict('os.environ', env_vars):
        module = load_handler_module()
        if hasattr(module, '_clients'):
            setattr(module, '_clients', {})
        if hasattr(module, '_github_token_cache'):
            setattr(module, '_github_token_cache', {'value': None})
        if hasattr(module, '_dependencies_validated'):
            deps = {'checked': True, 'valid': True, 'errors': []}
            setattr(module, '_dependencies_validated', deps)
        yield module


@pytest.fixture
def ecs_runner_post_event_factory():
    """Factory to create ECS runner POST event payloads."""
    def _create_event(job_id=123, job_labels=None, github_repo='test/repo'):
        if job_labels is None:
            job_labels = ['fargate', 'self-hosted']
        return {
            'path': '/v1/ecs-runner',
            'httpMethod': 'POST',
            'body': json.dumps({
                'job_id': job_id,
                'job_labels': job_labels,
                'github_repo': github_repo
            })
        }
    return _create_event


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
        return Mock()
    return mock_client


def create_fargate_runner_env(use_spot=None):
    """Create standard environment dict for fargate runner tests."""
    env = {
        'ECS_CLUSTER': 'test-cluster',
        'TASK_DEFINITION': 'test-task',
        'SUBNETS': 'subnet-1',
        'SECURITY_GROUPS': 'sg-1',
        'CONTAINER_NAME': 'test-container',
        'GITHUB_TOKEN_SECRET_NAME': '/test/token'
    }
    if use_spot is not None:
        env['USE_SPOT'] = 'true' if use_spot else 'false'
    return env


def create_mock_ssm_with_token(token_value='test-token'):
    """Create a mock SSM client that returns the given token."""
    mock_ssm = Mock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': token_value}}
    return mock_ssm


def create_mock_ecs_with_run_task(task_arn='test-arn'):
    """Create a mock ECS client that returns success from run_task."""
    mock_ecs = Mock()
    mock_ecs.run_task.return_value = {'tasks': [{'taskArn': task_arn}]}
    return mock_ecs


def create_mock_ecs_for_status(task_arns=None):
    """Create a mock ECS client for status checks."""
    mock_ecs = Mock()
    mock_ecs.list_tasks.return_value = {'taskArns': task_arns or []}
    return mock_ecs
