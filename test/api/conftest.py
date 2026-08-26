from unittest.mock import Mock

import boto3
import pytest
import requests

from repo_utils import REPO_ROOT
from test_fixtures.terraform import terraform_init, terraform_output


API_COMMON_ROUTING_DIR = REPO_ROOT / "src" / "api" / "common" / "routing"


@pytest.fixture(scope="session")
def api_common_routing_terraform_initialized():
    return terraform_init(API_COMMON_ROUTING_DIR)


@pytest.fixture(scope="session")
def api_common_routing_outputs(request):
    if not request.getfixturevalue("api_common_routing_terraform_initialized"):
        pytest.skip("Terraform init failed for api_common_routing")
    return {
        "api_gateway_id": terraform_output(
            API_COMMON_ROUTING_DIR, "api_gateway_id"
        ),
    }


@pytest.fixture(scope="session")
def apigateway_client(aws_region):
    return boto3.client("apigateway", region_name=aws_region)


@pytest.fixture(scope="session")
def ses_client(aws_region):
    return boto3.client("ses", region_name=aws_region)


def endpoint_is_deployed(api_url: str, path: str, method: str = "GET") -> bool:
    url = f"{api_url}{path}"
    headers = {"x-test-mode": "true"}
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        else:
            response = requests.post(url, headers=headers, json={}, timeout=5)
        if response.status_code == 404:
            return False
        if response.status_code == 500:
            return False
        try:
            body = response.json()
            if body.get("error") == "Not Found":
                return False
        except (ValueError, KeyError):
            pass
        return True
    except requests.exceptions.RequestException:
        return False


def skip_if_endpoint_not_deployed(api_url: str, path: str, method: str = "GET"):
    if not endpoint_is_deployed(api_url, path, method):
        pytest.skip(f"Endpoint {path} not deployed (managed by separate workflow)")


@pytest.fixture
def lambda_context():
    return Mock()


@pytest.fixture(scope="session")
def lambda_client(aws_region):
    return boto3.client("lambda", region_name=aws_region)
