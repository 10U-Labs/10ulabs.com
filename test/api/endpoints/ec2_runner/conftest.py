import os
import re
from pathlib import Path
from test.api.conftest import get_runner_labels, parse_shared_module_outputs
from typing import Any, Dict

import boto3
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
EC2_RUNNER_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "ec2_runner"


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
    ec2_runner_locals_path = REPO_ROOT / "src" / "api" / "endpoints" / "ec2_runner" / "locals.tf"
    config = parse_locals_file(api_locals_path, shared)
    ec2_runner_locals = parse_locals_file(ec2_runner_locals_path, shared)
    config.update(ec2_runner_locals)
    config['api_fqdn'] = f"api.{shared.get('domain_name', '')}"
    config['github_repo_full'] = f"{shared.get('github_org', '')}/{shared.get('name_for_github_repo', '')}"
    return config


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
    ec2_runner_tfvars_path = REPO_ROOT / "src" / "api" / "endpoints" / "ec2_runner" / "terraform.tfvars"
    result = parse_tfvars(api_tfvars_path)
    ec2_runner_vars = parse_tfvars(ec2_runner_tfvars_path)
    result.update(ec2_runner_vars)
    api_locals = parse_api_locals()
    result['aws_region'] = api_locals.get('aws_region', '')
    result['api_fqdn'] = api_locals.get('api_fqdn', '')
    result['github_repo'] = api_locals.get('github_repo_full', '')
    result['resource_prefix'] = api_locals.get('resource_prefix', '')
    result['ec2_runner_ami_purpose_tag'] = api_locals.get('ec2_runner_ami_purpose_tag', '')
    result['ec2_runner_ami_purpose_value'] = api_locals.get('ec2_runner_ami_purpose_value', '')
    result['ec2_runner_ami_stable_tag'] = api_locals.get('ec2_runner_ami_stable_tag', '')
    result['ssm_parameter_name_for_github_pat'] = os.environ.get(
        'SSM_PARAMETER_NAME_FOR_GITHUB_PAT', '/test/github/pat'
    )
    result['ssm_parameter_name_for_api_key'] = result.get('ssm_parameter_name_for_api_key', '/api/key')
    runner_labels = get_runner_labels()
    result.update(runner_labels)
    return result


@pytest.fixture
def ec2_client():
    return boto3.client('ec2', region_name='us-east-1')


@pytest.fixture
def dynamodb_client():
    return boto3.client('dynamodb', region_name='us-east-1')
