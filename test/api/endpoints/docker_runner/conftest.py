import importlib.util
import json
import os
import re
from pathlib import Path
from types import ModuleType
from typing import Any, Dict
from unittest.mock import Mock, patch
import boto3
import pytest
import yaml


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
DOCKER_RUNNER_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "docker_runner"


def parse_shared_module_outputs() -> Dict[str, str]:
    outputs_path = REPO_ROOT / "lib" / "terraform" / "outputs.tf"
    config = {}
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()
    pattern = r'output\s+"([^"]+)"\s*\{\s*value\s*=\s*"([^"]+)"'
    matches = re.findall(pattern, content)
    for key, value in matches:
        config[key] = value
    return config


def parse_locals_file(locals_path: Path, shared: Dict[str, str]) -> Dict[str, str]:
    config: Dict[str, str] = {}
    with open(locals_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#') and not line.startswith('locals'):
                match = re.match(r'(\w+)\s*=\s*(.+)', line)
                if match:
                    key, value = match.groups()
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        config[key] = value[1:-1]
                    elif 'module.shared.' in value:
                        ref = value.replace('module.shared.', '').strip()
                        config[key] = shared.get(ref, '')
    return config


def parse_api_locals() -> Dict[str, str]:
    shared = parse_shared_module_outputs()
    api_locals_path = REPO_ROOT / "src" / "api" / "backend" / "locals.tf"
    docker_runner_locals_path = REPO_ROOT / "src" / "api" / "endpoints" / "docker_runner" / "locals.tf"
    config = parse_locals_file(api_locals_path, shared)
    docker_runner_locals = parse_locals_file(docker_runner_locals_path, shared)
    config.update(docker_runner_locals)
    config['api_fqdn'] = f"api.{shared.get('domain_name', '')}"
    config['github_repo_full'] = f"{shared.get('github_org', '')}/{shared.get('name_for_github_repo', '')}"
    return config


def parse_shared_config() -> Dict[str, Any]:
    config_path = REPO_ROOT / "etc" / "runners.yml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_tfvars(tfvars_path: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    with open(tfvars_path, encoding="utf-8") as f:
        content = f.read()
    list_pattern = r'(\w+)\s*=\s*\[([^\]]*)\]'
    for match in re.finditer(list_pattern, content, re.DOTALL):
        key = match.group(1)
        values_str = match.group(2)
        values = [v.strip().strip('"') for v in values_str.split(',') if v.strip()]
        result[key] = values
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith("#") and '=' in line and '[' not in line:
            line_match = re.match(r'(\w+)\s*=\s*"?([^"]+)"?', line)
            if line_match:
                key, value = line_match.groups()
                if key not in result:
                    result[key] = value.strip('"')
    return result


@pytest.fixture(name="config", scope="module")
def config_fixture() -> Dict[str, Any]:
    api_tfvars_path = REPO_ROOT / "src" / "api" / "backend" / "terraform.tfvars"
    result = parse_tfvars(api_tfvars_path)
    api_locals = parse_api_locals()
    result['aws_region'] = api_locals.get('aws_region', '')
    result['api_fqdn'] = api_locals.get('api_fqdn', '')
    result['github_repo'] = api_locals.get('github_repo_full', '')
    result['resource_prefix'] = api_locals.get('resource_prefix', '')
    result['ssm_parameter_name_for_github_pat'] = os.environ.get(
        'SSM_PARAMETER_NAME_FOR_GITHUB_PAT', '/test/github/pat'
    )
    result['ssm_parameter_name_for_api_key'] = result.get('ssm_parameter_name_for_api_key', '/api/key')
    result['ecr_repository_name'] = result.get('container_name', 'github-runner')
    shared_config = parse_shared_config()
    runner_labels = shared_config.get('runner_labels', {})
    result['runner_label_fargate_spot'] = runner_labels.get('fargate_spot', '')
    result['runner_label_fargate_spot_e2e_test'] = runner_labels.get('fargate_spot_e2e_test', '')
    return result


@pytest.fixture
def ecs_client():
    return boto3.client('ecs', region_name='us-east-1')


@pytest.fixture
def ecr_client():
    return boto3.client('ecr', region_name='us-east-1')


@pytest.fixture
def dynamodb_client():
    return boto3.client('dynamodb', region_name='us-east-1')


def parse_response_body(response: Dict[str, Any]) -> Any:
    return json.loads(response['body'])


def assert_response_status(response: Dict[str, Any], expected_code: int) -> None:
    assert response['statusCode'] == expected_code


def assert_json_content_type(response: Dict[str, Any]) -> None:
    assert response['headers']['Content-Type'].startswith('application/json')


def load_handler_module(relative_path: str, module_name: str) -> ModuleType:
    base_path = Path(__file__).parent.parent.parent.parent / "src" / "api"
    handler_path = base_path / relative_path
    spec = importlib.util.spec_from_file_location(module_name, handler_path)
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
        module = load_handler_module("endpoints/docker_runner/lambda/handler.py", "docker_runner_handler")
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
