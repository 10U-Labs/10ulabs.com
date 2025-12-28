"""Pytest fixtures for EC2 runner post-deployment tests."""
import random

from test.api.endpoints.conftest import parse_tfvars

import boto3
import pytest
import requests

from ..conftest import REPO_ROOT


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(shared_config):
    """Provide the API URL for tests."""
    domain = shared_config.get('domain_name', '')
    return f"https://api.{domain}"


def get_api_key_parameter_name():
    """Get the SSM parameter name for the API key from tfvars."""
    tfvars_path = REPO_ROOT / "src" / "api" / "shared" / "routing" / "terraform.tfvars"
    tfvars = parse_tfvars(tfvars_path)
    return tfvars.get('ssm_parameter_name_for_api_key', '/api/key')


def get_api_key():
    """Retrieve the API key from SSM Parameter Store."""
    ssm = boto3.client('ssm')
    parameter_name = get_api_key_parameter_name()
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    return response['Parameter']['Value']


def make_authenticated_get(url, api_key, timeout=30, **kwargs):
    """Make an authenticated GET request with the API key header."""
    headers = kwargs.pop('headers', {})
    headers['x-api-key'] = api_key
    return requests.get(url, headers=headers, timeout=timeout, **kwargs)


def make_authenticated_post(url, api_key, timeout=30, **kwargs):
    """Make an authenticated POST request with the API key header."""
    headers = kwargs.pop('headers', {})
    headers['x-api-key'] = api_key
    return requests.post(url, headers=headers, timeout=timeout, **kwargs)


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture():
    """Provide the API key for tests."""
    return get_api_key()


@pytest.fixture(scope="module")
def ec2_client(aws_region):
    """Provide an EC2 client."""
    return boto3.client('ec2', region_name=aws_region)


@pytest.fixture(scope="module")
def dynamodb_client(aws_region):
    """Provide a DynamoDB client."""
    return boto3.client('dynamodb', region_name=aws_region)


def create_runner_job_payload(github_repo, job_labels, run_id=None):
    """Create a runner job payload with a random job ID."""
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
