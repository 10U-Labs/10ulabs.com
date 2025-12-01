import os
from pathlib import Path

from test.api.endpoints.ec2_runner.conftest import (
    parse_api_locals,
    parse_shared_module_outputs,
)

import pytest
import yaml


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent


def parse_shared_config():
    config_path = REPO_ROOT / "etc" / "runners.yml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


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
