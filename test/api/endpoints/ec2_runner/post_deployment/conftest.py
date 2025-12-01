import os
import random
import re
from pathlib import Path

import boto3
import pytest
import requests


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent


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


def get_api_url():
    shared = parse_shared_module_outputs()
    domain = shared.get('domain_name', '')
    return f"https://api.{domain}"


def get_api_key():
    ssm = boto3.client('ssm')
    shared = parse_shared_module_outputs()
    resource_prefix = shared.get('resource_prefix', '')
    parameter_name = f"/github-runner/{resource_prefix}/api-key"
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    return response['Parameter']['Value']


def make_authenticated_get(url, api_key, **kwargs):
    headers = kwargs.pop('headers', {})
    headers['x-api-key'] = api_key
    return requests.get(url, headers=headers, **kwargs)


def make_authenticated_post(url, api_key, **kwargs):
    headers = kwargs.pop('headers', {})
    headers['x-api-key'] = api_key
    return requests.post(url, headers=headers, **kwargs)


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture():
    return get_api_url()


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture():
    return get_api_key()


@pytest.fixture
def ec2_client():
    return boto3.client('ec2', region_name='us-east-1')


@pytest.fixture
def dynamodb_client():
    return boto3.client('dynamodb', region_name='us-east-1')


def create_runner_job_payload(github_repo, job_labels, run_id=None):
    job_id = random.randint(10000000, 99999999)
    payload = {
        'job_id': job_id,
        'github_repo': github_repo,
        'job_labels': job_labels,
        'runner_type': 'ec2'
    }
    if run_id:
        payload['run_id'] = run_id
    return job_id, payload
