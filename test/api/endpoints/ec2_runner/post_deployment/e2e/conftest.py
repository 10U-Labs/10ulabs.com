import os
import re
from pathlib import Path

import boto3
import pytest
import yaml

from test.api.endpoints.ec2_runner.post_deployment.conftest import (
    api_key_fixture,
    api_url_fixture,
    create_runner_job_payload,
    make_authenticated_get,
    make_authenticated_post,
)


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent


def parse_shared_config():
    config_path = REPO_ROOT / "etc" / "runners.yml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_shared_module_outputs():
    outputs_path = REPO_ROOT / "lib" / "terraform" / "outputs.tf"
    config = {}
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()
    pattern = r'output\s+"([^"]+)"\s*\{\s*value\s*=\s*"([^"]+)"'
    matches = re.findall(pattern, content)
    for key, value in matches:
        config[key] = value
    return config


def parse_api_locals():
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
    return config


@pytest.fixture(name="config", scope="module")
def config_fixture():
    shared = parse_shared_module_outputs()
    api_locals = parse_api_locals()
    shared_config = parse_shared_config()
    runner_labels = shared_config.get('runner_labels', {})
    return {
        'github_repo': f"{shared.get('github_org', '')}/{shared.get('name_for_github_repo', '')}",
        'runner_label_ec2_spot_e2e_test': runner_labels.get('ec2_spot_e2e_test', ''),
        'ec2_runner_ami_purpose_tag': api_locals.get('ec2_runner_ami_purpose_tag', 'Purpose'),
        'ec2_runner_ami_purpose_value': api_locals.get('ec2_runner_ami_purpose_value', 'GitHub self-hosted EC2 runner'),
        'ec2_runner_ami_stable_tag': api_locals.get('ec2_runner_ami_stable_tag', 'Stable'),
        'resource_prefix': shared.get('resource_prefix', ''),
    }


@pytest.fixture(name="workflow_runners_table_name", scope="module")
def workflow_runners_table_name_fixture(config):
    return f"{config['resource_prefix']}-workflow-runners"


@pytest.fixture(name="test_context", scope="module")
def test_context_fixture(api_url, api_key, config):
    github_run_id = os.environ.get('GITHUB_RUN_ID', '0')
    return {
        'api_credentials': {'url': api_url, 'key': api_key},
        'github_repo': config['github_repo'],
        'github_run_id': int(github_run_id) if github_run_id else 0
    }


api_url = api_url_fixture
api_key = api_key_fixture
