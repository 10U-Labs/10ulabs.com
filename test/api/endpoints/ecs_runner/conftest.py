"""Shared pytest fixtures and utilities for ECS runner tests."""
import importlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

from test.api.conftest import get_runner_labels
from test.api.endpoints.conftest import parse_locals_file, parse_tfvars

import boto3
import pytest
from repo_utils import REPO_ROOT

ECS_RUNNER_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "ecs_runner"
RUNNERS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "runners"


def terraform_output(directory: Path, name: str) -> str:
    """Get a terraform output value from the specified directory."""
    result = subprocess.run(
        ["terraform", "output", "-raw", name],
        cwd=str(directory),
        capture_output=True,
        text=True,
        check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""

# Add lib/python to path for unit tests that use --confcutdir
LIB_DIR = REPO_ROOT / "lib" / "python"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))


def _get_shared_config() -> Dict[str, str]:
    """Load and return shared config using dynamic import."""
    terraform_config = importlib.import_module("terraform_config")
    return terraform_config.get_shared_config()


@pytest.fixture(name="shared_config", scope="session")
def shared_config_fixture() -> Dict[str, str]:
    """Provide shared config for tests using --confcutdir."""
    return _get_shared_config()


def _parse_api_locals(shared_config: Dict[str, str]) -> Dict[str, str]:
    """Parse API and ECS runner locals files to build configuration."""
    api_locals_path = REPO_ROOT / "src" / "api" / "backend" / "locals.tf"
    ecs_runner_locals_path = REPO_ROOT / "src" / "api" / "endpoints" / "ecs_runner" / "locals.tf"
    config = parse_locals_file(api_locals_path, shared_config)
    ecs_runner_locals = parse_locals_file(ecs_runner_locals_path, shared_config)
    config.update(ecs_runner_locals)
    config['api_fqdn'] = f"api.{shared_config.get('domain_name', '')}"
    github_org = shared_config.get('github_org', '')
    github_repo_name = shared_config.get('name_for_github_repo', '')
    config['github_repo_full'] = f"{github_org}/{github_repo_name}"
    return config


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, Any]:
    """Provide configuration dictionary from Terraform files."""
    api_tfvars_path = REPO_ROOT / "src" / "api" / "backend" / "terraform.tfvars"
    result = parse_tfvars(api_tfvars_path)
    api_locals = _parse_api_locals(shared_config)
    result['aws_region'] = api_locals.get('aws_region', '')
    result['api_fqdn'] = api_locals.get('api_fqdn', '')
    result['github_repo'] = api_locals.get('github_repo_full', '')
    result['resource_prefix'] = api_locals.get('resource_prefix', '')
    result['ssm_parameter_name_for_github_pat'] = os.environ.get(
        'SSM_PARAMETER_NAME_FOR_GITHUB_PAT', '/test/github/pat'
    )
    api_key_param = result.get('ssm_parameter_name_for_api_key', '/api/key')
    result['ssm_parameter_name_for_api_key'] = api_key_param
    result['ecr_repository_name'] = shared_config['ecr_repository_name_runners']
    resource_prefix = shared_config.get('resource_prefix', 'TenULabs')
    result['workflow_runners_table_name'] = f"{resource_prefix}-workflow-runners"
    ecs_runner_tfvars = parse_tfvars(ECS_RUNNER_SRC / "terraform.tfvars")
    result['cluster_name'] = ecs_runner_tfvars.get('cluster_name', '')
    result['container_name'] = ecs_runner_tfvars.get('container_name', '')
    result['task_family'] = ecs_runner_tfvars.get('task_family', '')
    runner_labels = get_runner_labels()
    result.update(runner_labels)
    result['api_version'] = 'v1'
    lambda_names = shared_config.get('lambda_handler_names', {})
    result['lambda_function_name'] = lambda_names.get('ecs_runner', '')
    return result


@pytest.fixture(scope="session")
def ecs_client(aws_region):
    """Provide ECS client for tests."""
    return boto3.client('ecs', region_name=aws_region)


@pytest.fixture(scope="session")
def dynamodb_client(aws_region):
    """Provide DynamoDB client for tests."""
    return boto3.client('dynamodb', region_name=aws_region)
