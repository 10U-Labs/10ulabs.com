from unittest.mock import Mock

import boto3
from botocore.exceptions import ClientError
import pytest

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


@pytest.fixture
def lambda_context():
    return Mock()


@pytest.fixture(scope="session")
def lambda_client(aws_region):
    return boto3.client("lambda", region_name=aws_region)


@pytest.fixture(scope="session")
def iam_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("iam", region_name=region)


@pytest.fixture(scope="session")
def ssm_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("ssm", region_name=region)


@pytest.fixture(scope="session")
def logs_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("logs", region_name=region)


@pytest.fixture(scope="module")
def api_gateway_info(request):
    client = request.getfixturevalue("apigateway_client")
    api_common_routing_outputs = request.getfixturevalue("api_common_routing_outputs")

    api_id = api_common_routing_outputs.get("api_gateway_id")
    if not api_id:
        return {"id": None, "exists": False, "accessible": False}

    try:
        response = client.get_rest_api(restApiId=api_id)
        endpoint_config = response.get("endpointConfiguration", {})
        paginator = client.get_paginator("get_resources")
        paths = []
        for page in paginator.paginate(restApiId=api_id):
            paths.extend([r.get("path", "") for r in page.get("items", [])])
        return {
            "id": api_id,
            "exists": True,
            "accessible": True,
            "endpoint_types": endpoint_config.get("types", []),
            "paths": paths
        }
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDeniedException":
            return {"id": api_id, "exists": None, "accessible": False}
        if error_code == "NotFoundException":
            return {"id": api_id, "exists": False, "accessible": True}
        raise
