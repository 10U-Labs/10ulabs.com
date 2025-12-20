"""Pytest fixtures for EC2 runner tests."""
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

EC2_RUNNER_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "ec2_runner"


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
    """Parse API and EC2 runner locals files into a config dict."""
    api_locals_path = REPO_ROOT / "src" / "api" / "backend" / "locals.tf"
    ec2_locals_path = REPO_ROOT / "src" / "api" / "endpoints" / "ec2_runner" / "locals.tf"
    config = parse_locals_file(api_locals_path, shared_config)
    ec2_runner_locals = parse_locals_file(ec2_locals_path, shared_config)
    config.update(ec2_runner_locals)
    config['api_fqdn'] = f"api.{shared_config.get('domain_name', '')}"
    github_org = shared_config.get('github_org', '')
    repo_name = shared_config.get('name_for_github_repo', '')
    config['github_repo_full'] = f"{github_org}/{repo_name}"
    return config


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, Any]:
    """Provide configuration for EC2 runner tests."""
    api_tfvars_path = REPO_ROOT / "src" / "api" / "backend" / "terraform.tfvars"
    ec2_tfvars_path = (
        REPO_ROOT / "src" / "api" / "endpoints" / "ec2_runner" / "terraform.tfvars"
    )
    result = parse_tfvars(api_tfvars_path)
    ec2_runner_vars = parse_tfvars(ec2_tfvars_path)
    result.update(ec2_runner_vars)
    api_locals = _parse_api_locals(shared_config)
    result['aws_region'] = api_locals.get('aws_region', '')
    result['api_fqdn'] = api_locals.get('api_fqdn', '')
    result['github_repo'] = api_locals.get('github_repo_full', '')
    result['resource_prefix'] = api_locals.get('resource_prefix', '')
    result['ec2_runner_ami_purpose_tag'] = api_locals.get('ec2_runner_ami_purpose_tag', '')
    result['ec2_runner_ami_purpose_value'] = api_locals.get(
        'ec2_runner_ami_purpose_value', ''
    )
    result['ec2_runner_ami_stable_tag'] = api_locals.get('ec2_runner_ami_stable_tag', '')
    result['ssm_parameter_name_for_github_pat'] = os.environ.get(
        'SSM_PARAMETER_NAME_FOR_GITHUB_PAT', '/test/github/pat'
    )
    result['ssm_parameter_name_for_api_key'] = result.get(
        'ssm_parameter_name_for_api_key', '/api/key'
    )
    runner_labels = get_runner_labels()
    result.update(runner_labels)
    return result


@pytest.fixture
def ec2_client(aws_region):
    """Provide an EC2 client."""
    return boto3.client('ec2', region_name=aws_region)


@pytest.fixture
def dynamodb_client(aws_region):
    """Provide a DynamoDB client."""
    return boto3.client('dynamodb', region_name=aws_region)
