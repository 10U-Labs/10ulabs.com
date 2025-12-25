"""Shared pytest fixtures and utilities for ECS runner tests."""
import os
from typing import Any, Dict

from test.api.conftest import get_runner_labels

import pytest
from repo_utils import REPO_ROOT
from test_fixtures import get_shared_config, get_tfvars_values, get_endpoint_local_values
from test_fixtures.terraform import terraform_output

ECS_RUNNER_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "ecs_runner"
API_BACKEND_SRC = REPO_ROOT / "src" / "api" / "backend"

# Use shared AWS fixtures (provides ecs_client, dynamodb_client, etc.)
pytest_plugins = ['test_fixtures.aws']


@pytest.fixture(name="shared_config", scope="session")
def shared_config_fixture() -> Dict[str, str]:
    """Provide shared config for tests using --confcutdir."""
    return get_shared_config()


def _get_ecs_runner_locals(shared_config: Dict[str, str]) -> Dict[str, str]:
    """Get ECS runner locals using terraform_config (single source of truth)."""
    config = get_endpoint_local_values(API_BACKEND_SRC)
    config.update(get_endpoint_local_values(ECS_RUNNER_SRC))
    config['api_fqdn'] = f"api.{shared_config['domain_name']}"
    config['github_repo_full'] = f"{shared_config['github_org']}/{shared_config['name_for_github_repo']}"
    return config


@pytest.fixture(name="config", scope="session")
def config_fixture(shared_config) -> Dict[str, Any]:
    """Provide configuration dictionary from Terraform files."""
    result: Dict[str, Any] = get_tfvars_values(API_BACKEND_SRC)
    ecs_locals = _get_ecs_runner_locals(shared_config)
    result['aws_region'] = shared_config['aws_region']
    result['api_fqdn'] = ecs_locals['api_fqdn']
    result['github_repo'] = ecs_locals['github_repo_full']
    result['resource_prefix'] = ecs_locals.get('resource_prefix', '')
    result['ssm_parameter_name_for_github_pat'] = os.environ.get(
        'SSM_PARAMETER_NAME_FOR_GITHUB_PAT', '/test/github/pat'
    )
    result['ssm_parameter_name_for_api_key'] = result.get(
        'ssm_parameter_name_for_api_key', '/api/key'
    )
    result['ecr_repository_name'] = shared_config['ecr_repository_name_runners']
    result['workflow_runners_table_name'] = f"{shared_config['resource_prefix']}-workflow-runners"
    ecs_tfvars = get_tfvars_values(ECS_RUNNER_SRC)
    result['cluster_name'] = ecs_tfvars.get('cluster_name', '')
    result['container_name'] = ecs_tfvars.get('container_name', '')
    result['task_family'] = ecs_tfvars.get('task_family', '')
    result.update(get_runner_labels())
    result['api_version'] = 'v1'
    lambda_names = shared_config.get('lambda_handler_names', {})
    result['lambda_function_name'] = lambda_names.get('ecs_runner', '')
    return result
