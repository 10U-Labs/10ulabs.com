import os
from test.api.conftest import get_runner_labels, parse_shared_module_outputs

import pytest

from ...conftest import parse_api_locals


@pytest.fixture(name="config", scope="module")
def config_fixture():
    shared = parse_shared_module_outputs()
    api_locals = parse_api_locals()
    runner_labels = get_runner_labels()
    result = {
        'github_repo': f"{shared.get('github_org', '')}/{shared.get('name_for_github_repo', '')}",
        'ec2_runner_ami_purpose_tag': api_locals.get('ec2_runner_ami_purpose_tag', 'Purpose'),
        'ec2_runner_ami_purpose_value': api_locals.get('ec2_runner_ami_purpose_value', 'GitHub self-hosted EC2 runner'),
        'ec2_runner_ami_stable_tag': api_locals.get('ec2_runner_ami_stable_tag', 'Stable'),
        'resource_prefix': shared.get('resource_prefix', ''),
    }
    result.update(runner_labels)
    return result


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
