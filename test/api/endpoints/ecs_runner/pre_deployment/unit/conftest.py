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
