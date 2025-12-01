import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
DOCKER_RUNNER_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "docker_runner"


def load_handler_module() -> ModuleType:
    handler_path = DOCKER_RUNNER_SRC / "lambda" / "handler.py"
    spec = importlib.util.spec_from_file_location("docker_runner_handler", handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def docker_runner_handler(config: Dict[str, str]) -> Any:
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
            setattr(module, '_dependencies_validated', {'checked': True, 'valid': True, 'errors': []})
        yield module


@pytest.fixture
def lambda_context():
    return Mock()


@pytest.fixture
def docker_runner_post_event_factory():
    def _create_event(job_id=123, job_labels=None, github_repo='test/repo'):
        if job_labels is None:
            job_labels = ['fargate', 'self-hosted']
        return {
            'path': '/v1/docker-runner',
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
    def _create_response(read_value=b'', status=200, json_data=None):
        mock_response = Mock()
        if json_data is not None:
            mock_response.read.return_value = json.dumps(json_data).encode()
        else:
            mock_response.read.return_value = read_value
        mock_response.status = status
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        return mock_response
    return _create_response


def parse_response_body(response: Dict[str, Any]) -> Any:
    return json.loads(response['body'])


def assert_response_status(response: Dict[str, Any], expected_code: int) -> None:
    assert response['statusCode'] == expected_code


def assert_json_content_type(response: Dict[str, Any]) -> None:
    assert response['headers']['Content-Type'].startswith('application/json')
