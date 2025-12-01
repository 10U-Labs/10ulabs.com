import random

import boto3
import pytest
import requests

from ..conftest import parse_shared_module_outputs, parse_tfvars, REPO_ROOT


def get_api_url():
    shared = parse_shared_module_outputs()
    domain = shared.get('domain_name', '')
    return f"https://api.{domain}"


def get_api_key_parameter_name():
    tfvars_path = REPO_ROOT / "src" / "api" / "backend" / "terraform.tfvars"
    tfvars = parse_tfvars(tfvars_path)
    return tfvars.get('ssm_parameter_name_for_api_key', '/api/key')


def get_api_key():
    ssm = boto3.client('ssm')
    parameter_name = get_api_key_parameter_name()
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    return response['Parameter']['Value']


def make_authenticated_get(url, api_key, timeout=30, **kwargs):
    headers = kwargs.pop('headers', {})
    headers['x-api-key'] = api_key
    return requests.get(url, headers=headers, timeout=timeout, **kwargs)


def make_authenticated_post(url, api_key, timeout=30, **kwargs):
    headers = kwargs.pop('headers', {})
    headers['x-api-key'] = api_key
    return requests.post(url, headers=headers, timeout=timeout, **kwargs)


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
