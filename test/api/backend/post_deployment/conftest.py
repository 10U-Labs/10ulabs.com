"""Pytest fixtures for post-deployment integration tests."""
import os
import time
import boto3
import pytest
import requests


DEFAULT_REQUEST_TIMEOUT = 10
DOCKER_RUNNER_REQUEST_TIMEOUT = 30


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture(config):
    """Provide AWS region from config."""
    return config["aws_region"]


@pytest.fixture(name="ssm_client", scope="module")
def ssm_client_fixture(aws_region):
    """Provide SSM client for the configured region."""
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(name="ec2_client", scope="module")
def ec2_client_fixture(aws_region):
    """Provide EC2 client for the configured region."""
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(name="ecr_client", scope="module")
def ecr_client_fixture(aws_region):
    """Provide ECR client for the configured region."""
    return boto3.client("ecr", region_name=aws_region)


@pytest.fixture(name="ecs_client", scope="module")
def ecs_client_fixture(aws_region):
    """Provide ECS client for the configured region."""
    return boto3.client("ecs", region_name=aws_region)


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    """Provide the API base URL."""
    return f"https://{config['api_fqdn']}"


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture(ssm_client):
    """Retrieve API key from SSM Parameter Store."""
    param_response = ssm_client.get_parameter(Name='/api/key', WithDecryption=True)
    return param_response['Parameter']['Value'] if param_response else None


def make_health_check_request(api_url, api_key):
    """Make a health check request to the runners endpoint."""
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    return requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)


def assert_circuit_breaker_state_in_response(response):
    """Assert that circuit breaker state is present in the response."""
    data = response.json()
    assert data["circuit_breaker"] is not None


def make_authenticated_get(url, api_key, timeout=DEFAULT_REQUEST_TIMEOUT):
    """Make an authenticated GET request with test mode enabled."""
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    return requests.get(url, headers=headers, timeout=timeout)


def make_authenticated_post(url, api_key, json=None, timeout=DEFAULT_REQUEST_TIMEOUT):
    """Make an authenticated POST request with test mode enabled."""
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    return requests.post(url, json=json, headers=headers, timeout=timeout)


def make_e2e_get(url, api_key, timeout=DEFAULT_REQUEST_TIMEOUT):
    """Make an end-to-end GET request without test mode."""
    headers = {"x-api-key": api_key}
    return requests.get(url, headers=headers, timeout=timeout)


def make_e2e_post(url, api_key, json=None, timeout=DEFAULT_REQUEST_TIMEOUT):
    """Make an end-to-end POST request without test mode."""
    headers = {"x-api-key": api_key}
    return requests.post(url, json=json, headers=headers, timeout=timeout)


@pytest.fixture(name="github_repo", scope="module")
def github_repo_fixture(config):
    """Provide the GitHub repository name from config."""
    return config["github_repo"]


@pytest.fixture(name="cluster_name", scope="module")
def cluster_name_fixture(config):
    """Provide the ECS cluster name from config."""
    return config["cluster_name"]


@pytest.fixture(name="api_credentials", scope="module")
def api_credentials_fixture(api_url, api_key):
    """Provide API credentials as a dictionary."""
    return {"url": api_url, "key": api_key}


@pytest.fixture(name="github_run_id", scope="module")
def github_run_id_fixture():
    """Provide the GitHub Actions run ID from environment."""
    return os.environ.get("GITHUB_RUN_ID")


@pytest.fixture(name="dynamodb_client", scope="module")
def dynamodb_client_fixture(aws_region):
    """Provide DynamoDB client for the configured region."""
    return boto3.client("dynamodb", region_name=aws_region)


@pytest.fixture(name="workflow_runners_table_name", scope="module")
def workflow_runners_table_name_fixture(config):
    """Provide the workflow runners DynamoDB table name."""
    return config["workflow_runners_table_name"]


@pytest.fixture(name="ecr_image_count", scope="module")
def ecr_image_count_fixture(ecr_client, config):
    """Count ECR images with the stable tag."""
    response = ecr_client.describe_images(
        repositoryName=config["ecr_repository_name"],
        filter={'tagStatus': 'TAGGED'}
    )
    stable_count = 0
    for image in response.get("imageDetails", []):
        if 'stable' in image.get('imageTags', []):
            stable_count += 1
    return stable_count


@pytest.fixture(name="ecr_has_latest_tag", scope="module")
def ecr_has_latest_tag_fixture(ecr_client, config):
    """Check if the ECR repository has an image with the latest tag."""
    response = ecr_client.list_images(repositoryName=config["ecr_repository_name"])
    image_tags = [img.get('imageTag') for img in response['imageIds'] if img.get('imageTag')]
    return 'latest' in image_tags


def create_runner_job_payload(github_repo, job_labels, run_id=None):
    """Create a payload for runner job requests."""
    job_id = int(time.time())
    payload = {
        "job_id": job_id,
        "job_labels": job_labels,
        "github_repo": github_repo,
        "run_id": int(run_id) if run_id else None
    }
    return job_id, payload


def get_ecs_task_tags(ecs_client, cluster_name, task_arn):
    """Retrieve tags for an ECS task."""
    response = ecs_client.describe_tasks(
        cluster=cluster_name,
        tasks=[task_arn],
        include=['TAGS']
    )
    tags = response['tasks'][0].get('tags', [])
    return {tag['key']: tag['value'] for tag in tags}


@pytest.fixture(name="test_context", scope="module")
def test_context_fixture(api_credentials, github_repo, github_run_id):
    """Provide combined test context with credentials and identifiers."""
    return {
        "api_credentials": api_credentials,
        "github_repo": github_repo,
        "github_run_id": github_run_id
    }


def query_workflow_runners_by_run_id(dynamodb_client, table_name, run_id):
    """Query workflow runners table by run ID."""
    response = dynamodb_client.query(
        TableName=table_name,
        KeyConditionExpression='run_id = :rid',
        ExpressionAttributeValues={':rid': {'S': str(run_id)}}
    )
    return response.get('Items', [])
