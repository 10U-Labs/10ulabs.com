import boto3
from botocore.exceptions import ClientError
import concurrent.futures
import pytest
import requests


DEFAULT_REQUEST_TIMEOUT = 10


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(tfvars):
    return f"https://{tfvars['domain_subdomain']}"


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture(tfvars):
    region = tfvars.get('aws_region', 'us-east-1')
    client = boto3.client('ssm', region_name=region)
    param_response = client.get_parameter(Name='/api/key', WithDecryption=True)
    return param_response['Parameter']['Value'] if param_response else None


@pytest.fixture(name="ecr_image_count", scope="module")
def ecr_image_count_fixture(tfvars):
    region = tfvars.get('aws_region', 'us-east-1')
    ecr_client = boto3.client('ecr', region_name=region)
    try:
        response = ecr_client.describe_images(
            repositoryName='github-runner',
            filter={'tagStatus': 'TAGGED'}
        )
        stable_images = [
            img for img in response.get('imageDetails', [])
            if 'stable' in img.get('imageTags', [])
        ]
        return len(stable_images)
    except ClientError:
        return 0


def make_authenticated_get(url, api_key, timeout=DEFAULT_REQUEST_TIMEOUT):
    headers = {"x-api-key": api_key}
    return requests.get(url, headers=headers, timeout=timeout)


def make_authenticated_post(url, api_key, json=None, timeout=DEFAULT_REQUEST_TIMEOUT):
    headers = {"x-api-key": api_key}
    return requests.post(url, json=json, headers=headers, timeout=timeout)


def run_concurrent_requests(request_func, num_requests, max_workers=None):
    if max_workers is None:
        max_workers = num_requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(request_func) for _ in range(num_requests)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    return results
