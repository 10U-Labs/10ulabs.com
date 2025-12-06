"""Unit tests for conftest."""
import boto3
import pytest
import requests


DEFAULT_REQUEST_TIMEOUT = 10


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture(config):
    """Provide the AWS region from config."""
    return config["aws_region"]


@pytest.fixture(name="ssm_client", scope="module")
def ssm_client_fixture(aws_region):
    """Provide an SSM client for the configured region."""
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(name="sqs_client", scope="module")
def sqs_client_fixture(aws_region):
    """Provide an SQS client for the configured region."""
    return boto3.client("sqs", region_name=aws_region)


@pytest.fixture(name="ecs_client", scope="module")
def ecs_client_fixture(aws_region):
    """Provide an ECS client for the configured region."""
    return boto3.client("ecs", region_name=aws_region)


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    """Provide the API URL from config."""
    return f"https://{config['api_fqdn']}"


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture(ssm_client):
    """Retrieve the API key from SSM Parameter Store."""
    param_response = ssm_client.get_parameter(Name='/api/key', WithDecryption=True)
    result = None
    if param_response:
        result = param_response['Parameter']['Value']
    return result


@pytest.fixture(name="github_pat", scope="module")
def github_pat_fixture(ssm_client, config):
    """Retrieve the GitHub PAT from SSM Parameter Store."""
    param_name = config.get('ssm_parameter_name_for_github_pat')
    param_response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
    result = None
    if param_response:
        result = param_response['Parameter']['Value']
    return result


@pytest.fixture(name="github_repo", scope="module")
def github_repo_fixture(config):
    """Provide the GitHub repository from config."""
    return config["github_repo"]


def make_health_check_request(api_url, api_key):
    """Make an HTTP request to the health check endpoint."""
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    return requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)


def assert_circuit_breaker_state_in_response(response):
    """Assert that the response contains circuit breaker state."""
    data = response.json()
    assert data["circuit_breaker"] is not None


def create_test_dynamodb_item(client, table_name, item):
    """Create a test item in DynamoDB."""
    client.put_item(TableName=table_name, Item=item)


def cleanup_test_dynamodb_item(client, table_name, key):
    """Delete a test item from DynamoDB."""
    client.delete_item(TableName=table_name, Key=key)
