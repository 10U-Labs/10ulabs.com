"""Pytest fixtures for EC2 runner end-to-end tests."""
import os

from test.api.conftest import get_runner_labels

import pytest

from ...conftest import _parse_api_locals


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config):
    """Provide configuration for EC2 runner tests."""
    api_locals = _parse_api_locals(shared_config)
    runner_labels = get_runner_labels()
    github_org = shared_config.get('github_org', '')
    github_repo_name = shared_config.get('name_for_github_repo', '')
    result = {
        'github_repo': f"{github_org}/{github_repo_name}",
        'ec2_runner_ami_purpose_tag': api_locals.get('ec2_runner_ami_purpose_tag', 'Purpose'),
        'ec2_runner_ami_purpose_value': api_locals.get(
            'ec2_runner_ami_purpose_value', 'GitHub self-hosted EC2 runner'
        ),
        'ec2_runner_ami_stable_tag': api_locals.get('ec2_runner_ami_stable_tag', 'Stable'),
        'resource_prefix': shared_config.get('resource_prefix', ''),
    }
    result.update(runner_labels)
    return result


@pytest.fixture(name="test_context", scope="module")
def test_context_fixture(api_url, api_key, config):
    """Provide test context with API credentials and GitHub info."""
    github_run_id = os.environ.get('GITHUB_RUN_ID', '0')
    return {
        'api_credentials': {'url': api_url, 'key': api_key},
        'github_repo': config['github_repo'],
        'github_run_id': int(github_run_id) if github_run_id else 0
    }
