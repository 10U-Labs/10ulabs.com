import os
import re
from pathlib import Path
from typing import Any, Dict
import boto3
import pytest
import yaml


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
EC2_RUNNER_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "ec2_runner"


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


def parse_api_locals() -> Dict[str, str]:
    locals_path = REPO_ROOT / "src" / "api" / "backend" / "locals.tf"
    shared = parse_shared_module_outputs()
    config = {}
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
    config['api_fqdn'] = f"api.{shared.get('domain_name', '')}"
    config['github_repo_full'] = f"{shared.get('github_org', '')}/{shared.get('name_for_github_repo', '')}"
    return config


def parse_shared_config() -> Dict[str, Any]:
    config_path = REPO_ROOT / "etc" / "runners.yml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(name="config", scope="module")
def config_fixture() -> Dict[str, str]:
    tfvars_path = REPO_ROOT / "src" / "api" / "backend" / "terraform.tfvars"
    result = {}
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r'(\w+)\s*=\s*"?([^"]+)"?', line)
                if match:
                    key, value = match.groups()
                    result[key] = value.strip('"')
    shared = parse_shared_module_outputs()
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
    shared_config = parse_shared_config()
    runner_labels = shared_config.get('runner_labels', {})
    result['runner_label_ec2_spot'] = runner_labels.get('ec2_spot', '')
    result['runner_label_ec2_spot_e2e_test'] = runner_labels.get('ec2_spot_e2e_test', '')
    return result


@pytest.fixture
def ec2_client():
    return boto3.client('ec2', region_name='us-east-1')


@pytest.fixture
def dynamodb_client():
    return boto3.client('dynamodb', region_name='us-east-1')
