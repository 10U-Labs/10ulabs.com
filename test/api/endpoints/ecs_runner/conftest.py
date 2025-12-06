"""Shared pytest fixtures and utilities for ECS runner tests."""
# pylint: disable=duplicate-code
import json
import os
import re
from pathlib import Path
from test.api.conftest import get_runner_labels, parse_shared_module_outputs
from typing import Any, Dict

import boto3
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
ECS_RUNNER_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "ecs_runner"
RUNNERS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "runners"


def parse_locals_file(locals_path: Path, shared: Dict[str, str]) -> Dict[str, str]:
    """Parse Terraform locals file and extract configuration values."""
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
    """Parse API and ECS runner locals files to build configuration."""
    shared = parse_shared_module_outputs()
    api_locals_path = REPO_ROOT / "src" / "api" / "backend" / "locals.tf"
    ecs_runner_locals_path = REPO_ROOT / "src" / "api" / "endpoints" / "ecs_runner" / "locals.tf"
    config = parse_locals_file(api_locals_path, shared)
    ecs_runner_locals = parse_locals_file(ecs_runner_locals_path, shared)
    config.update(ecs_runner_locals)
    config['api_fqdn'] = f"api.{shared.get('domain_name', '')}"
    github_org = shared.get('github_org', '')
    github_repo_name = shared.get('name_for_github_repo', '')
    config['github_repo_full'] = f"{github_org}/{github_repo_name}"
    return config


def parse_tfvars(tfvars_path: Path) -> Dict[str, Any]:
    """Parse Terraform tfvars file and extract variable values."""
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
    """Provide configuration dictionary from Terraform files."""
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
    api_key_param = result.get('ssm_parameter_name_for_api_key', '/api/key')
    result['ssm_parameter_name_for_api_key'] = api_key_param
    shared = parse_shared_module_outputs()
    result['ecr_repository_name'] = shared.get('ecr_repository_name', '10ulabs')
    resource_prefix = shared.get('resource_prefix', 'TenULabs')
    result['workflow_runners_table_name'] = f"{resource_prefix}-workflow-runners"
    ecs_runner_tfvars = parse_tfvars(ECS_RUNNER_SRC / "terraform.tfvars")
    result['cluster_name'] = ecs_runner_tfvars.get('cluster_name', '')
    result['container_name'] = ecs_runner_tfvars.get('container_name', '')
    result['task_family'] = ecs_runner_tfvars.get('task_family', '')
    runner_labels = get_runner_labels()
    result.update(runner_labels)
    return result


@pytest.fixture
def ecs_client():
    """Provide ECS client for tests."""
    return boto3.client('ecs', region_name='us-east-1')


@pytest.fixture
def ecr_client():
    """Provide ECR client for tests."""
    return boto3.client('ecr', region_name='us-east-1')


@pytest.fixture
def dynamodb_client():
    """Provide DynamoDB client for tests."""
    return boto3.client('dynamodb', region_name='us-east-1')


def parse_response_body(response: Dict[str, Any]) -> Any:
    """Parse JSON body from Lambda response."""
    return json.loads(response['body'])


def assert_response_status(response: Dict[str, Any], expected_code: int) -> None:
    """Assert that response has expected status code."""
    assert response['statusCode'] == expected_code


def assert_json_content_type(response: Dict[str, Any]) -> None:
    """Assert that response has JSON content type."""
    assert response['headers']['Content-Type'].startswith('application/json')
