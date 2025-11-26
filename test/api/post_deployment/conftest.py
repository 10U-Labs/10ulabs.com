import time
import boto3
import pytest
import requests


DEFAULT_REQUEST_TIMEOUT = 10


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture(config):
    return config["aws_region"]


@pytest.fixture(name="ssm_client", scope="module")
def ssm_client_fixture(aws_region):
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(name="ec2_client", scope="module")
def ec2_client_fixture(aws_region):
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(name="ecr_client", scope="module")
def ecr_client_fixture(aws_region):
    return boto3.client("ecr", region_name=aws_region)


@pytest.fixture(name="ecs_client", scope="module")
def ecs_client_fixture(aws_region):
    return boto3.client("ecs", region_name=aws_region)


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    return f"https://{config['api_fqdn']}"


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture(ssm_client):
    param_response = ssm_client.get_parameter(Name='/api/key', WithDecryption=True)
    return param_response['Parameter']['Value'] if param_response else None


def make_health_check_request(api_url, api_key):
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    return requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)


def assert_circuit_breaker_state_in_response(response):
    data = response.json()
    assert data["circuit_breaker"] is not None


def make_authenticated_get(url, api_key, timeout=DEFAULT_REQUEST_TIMEOUT):
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    return requests.get(url, headers=headers, timeout=timeout)


def make_authenticated_post(url, api_key, json=None, timeout=DEFAULT_REQUEST_TIMEOUT):
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    return requests.post(url, json=json, headers=headers, timeout=timeout)


def make_e2e_get(url, api_key, timeout=DEFAULT_REQUEST_TIMEOUT):
    headers = {"x-api-key": api_key}
    return requests.get(url, headers=headers, timeout=timeout)


def make_e2e_post(url, api_key, json=None, timeout=DEFAULT_REQUEST_TIMEOUT):
    headers = {"x-api-key": api_key}
    return requests.post(url, json=json, headers=headers, timeout=timeout)


@pytest.fixture(name="github_repo", scope="module")
def github_repo_fixture(config):
    return config["github_repo"]


@pytest.fixture(name="cluster_name", scope="module")
def cluster_name_fixture(config):
    return config["cluster_name"]


@pytest.fixture(name="api_credentials", scope="module")
def api_credentials_fixture(api_url, api_key):
    return {"url": api_url, "key": api_key}


@pytest.fixture(name="ecr_image_count", scope="module")
def ecr_image_count_fixture(ecr_client, config):
    response = ecr_client.describe_images(repositoryName=config["ecr_repository"])
    return len(response.get("imageDetails", []))


def create_runner_job_payload(github_repo, job_labels):
    job_id = int(time.time())
    payload = {
        "job_id": job_id,
        "job_labels": job_labels,
        "github_repo": github_repo
    }
    return job_id, payload


def get_ecs_task_tags(ecs_client, cluster_name, task_arn):
    response = ecs_client.describe_tasks(
        cluster=cluster_name,
        tasks=[task_arn],
        include=['TAGS']
    )
    tags = response['tasks'][0].get('tags', [])
    return {tag['key']: tag['value'] for tag in tags}
