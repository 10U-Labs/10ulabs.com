import os
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


@pytest.fixture(name="sqs_client", scope="module")
def sqs_client_fixture(aws_region):
    return boto3.client("sqs", region_name=aws_region)


@pytest.fixture(name="ecs_client", scope="module")
def ecs_client_fixture(aws_region):
    return boto3.client("ecs", region_name=aws_region)


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(config):
    return f"https://{config['api_fqdn']}"


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture(ssm_client):
    param_response = ssm_client.get_parameter(Name='/api/key', WithDecryption=True)
    result = None
    if param_response:
        result = param_response['Parameter']['Value']
    return result


@pytest.fixture(name="github_pat", scope="module")
def github_pat_fixture():
    pat = os.environ.get("GITHUB_PAT")
    assert pat is not None
    return pat


@pytest.fixture(name="github_repo", scope="module")
def github_repo_fixture(config):
    return config["github_repo"]


def make_health_check_request(api_url, api_key):
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    return requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)


def assert_circuit_breaker_state_in_response(response):
    data = response.json()
    assert data["circuit_breaker"] is not None


def create_test_dynamodb_item(client, table_name, item):
    client.put_item(TableName=table_name, Item=item)


def cleanup_test_dynamodb_item(client, table_name, key):
    client.delete_item(TableName=table_name, Key=key)
