"""Pytest fixtures for EC2 runner tests."""
import os
from typing import Any, Dict

from test.api.conftest import get_runner_labels

import pytest
from repo_utils import REPO_ROOT
from test_fixtures import get_shared_config, get_tfvars_values, get_endpoint_local_values

EC2_RUNNER_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "ec2_runner"
API_BACKEND_SRC = REPO_ROOT / "src" / "api" / "backend"

# Use shared AWS fixtures (provides ec2_client, dynamodb_client, etc.)
pytest_plugins = ['test_fixtures.aws']


@pytest.fixture(name="shared_config", scope="session")
def shared_config_fixture() -> Dict[str, str]:
    """Provide shared config for tests using --confcutdir."""
    return get_shared_config()


def _get_ec2_runner_locals(shared_config: Dict[str, str]) -> Dict[str, str]:
    """Get EC2 runner locals using terraform_config (single source of truth)."""
    config = get_endpoint_local_values(API_BACKEND_SRC)
    config.update(get_endpoint_local_values(EC2_RUNNER_SRC))
    config['api_fqdn'] = f"api.{shared_config['domain_name']}"
    github_org = shared_config['github_org']
    github_repo = shared_config['name_for_github_repo']
    config['github_repo_full'] = f"{github_org}/{github_repo}"
    return config


# Alias for compatibility with e2e tests
_parse_api_locals = _get_ec2_runner_locals


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, Any]:
    """Provide configuration for EC2 runner tests."""
    result: Dict[str, Any] = get_tfvars_values(API_BACKEND_SRC)
    result.update(get_tfvars_values(EC2_RUNNER_SRC))
    ec2_locals = _get_ec2_runner_locals(shared_config)
    result['aws_region'] = shared_config['aws_region']
    result['api_fqdn'] = ec2_locals['api_fqdn']
    result['github_repo'] = ec2_locals['github_repo_full']
    result['resource_prefix'] = ec2_locals.get('resource_prefix', '')
    result['ec2_runner_ami_purpose_tag'] = ec2_locals.get('ec2_runner_ami_purpose_tag', '')
    result['ec2_runner_ami_purpose_value'] = ec2_locals.get('ec2_runner_ami_purpose_value', '')
    result['ec2_runner_ami_stable_tag'] = ec2_locals.get('ec2_runner_ami_stable_tag', '')
    result['ssm_parameter_name_for_github_pat'] = os.environ.get(
        'SSM_PARAMETER_NAME_FOR_GITHUB_PAT', '/test/github/pat'
    )
    result['ssm_parameter_name_for_api_key'] = result.get(
        'ssm_parameter_name_for_api_key', '/api/key'
    )
    result.update(get_runner_labels())
    return result
