"""Shared pytest fixtures and utilities for ECS runner tests."""
import os
from pathlib import Path
from typing import Any, Dict

from test.api.conftest import get_runner_labels, parse_shared_module_outputs
from test.api.endpoints.conftest import parse_locals_file, parse_tfvars

import boto3
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
ECS_RUNNER_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "ecs_runner"
RUNNERS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "runners"


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
    result['api_version'] = 'v1'
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
