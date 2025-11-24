from botocore.exceptions import ClientError
import concurrent.futures
import pytest
import requests


DEFAULT_REQUEST_TIMEOUT = 10


@pytest.fixture(name="ecr_image_count", scope="module")
def ecr_image_count_fixture(ecr_client):
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
