import boto3
import pytest
import requests


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture(tfvars):
    return tfvars["aws_region"]


@pytest.fixture(name="ssm_client", scope="module")
def ssm_client_fixture(aws_region):
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(name="ecr_client", scope="module")
def ecr_client_fixture(aws_region):
    return boto3.client("ecr", region_name=aws_region)


@pytest.fixture(name="ecs_client", scope="module")
def ecs_client_fixture(aws_region):
    return boto3.client("ecs", region_name=aws_region)


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(tfvars):
    return f"https://{tfvars['domain_subdomain']}"


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture(ssm_client):
    param_response = ssm_client.get_parameter(Name='/api/key', WithDecryption=True)
    return param_response['Parameter']['Value'] if param_response else None


def make_health_check_request(api_url, api_key):
    headers = {"x-api-key": api_key}
    return requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)


def assert_circuit_breaker_state_in_response(response):
    if response.status_code == 200:
        data = response.json()
        assert "circuit_breaker" in data or "status" in data
