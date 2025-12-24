"""Pytest fixtures for pre-deployment integration tests.

Common fixtures (api_backend_outputs, ecs_runner_outputs, apigateway_client,
sts_client, iam_client, lambda_client, s3_client) are inherited from
test/api/conftest.py and test_fixtures.aws.
"""
from botocore.exceptions import ClientError

from repo_utils import REPO_ROOT
from test_fixtures.terraform import terraform_init, terraform_output

import boto3
import pytest


pytest_plugins = ['pytest_layers']


WWW_SHARED_DIR = REPO_ROOT / "src" / "www" / "shared"


@pytest.fixture(scope="session")
def dynamodb_client(aws_region):
    """Create a DynamoDB client."""
    return boto3.client("dynamodb", region_name=aws_region)


@pytest.fixture(scope="module")
def api_gateway_info(apigateway_client, api_backend_outputs):
    """Get API Gateway info, handling missing/not-found cases gracefully."""
    api_id = api_backend_outputs.get("api_gateway_rest_api_id")
    if not api_id:
        return {"id": None, "exists": False, "accessible": False}

    try:
        response = apigateway_client.get_rest_api(restApiId=api_id)
        endpoint_config = response.get("endpointConfiguration", {})
        resources_response = apigateway_client.get_resources(restApiId=api_id)
        paths = [r.get("path", "") for r in resources_response.get("items", [])]
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


@pytest.fixture(scope="session")
def www_shared_terraform_initialized():
    """Initialize terraform for www_shared state access."""
    return terraform_init(WWW_SHARED_DIR)


@pytest.fixture(scope="session")
def www_shared_outputs(request):
    """Get www_shared terraform outputs."""
    if not request.getfixturevalue("www_shared_terraform_initialized"):
        pytest.skip("Terraform init failed for www_shared")
    return {
        "bucket_name": terraform_output(WWW_SHARED_DIR, "bucket_name"),
        "bucket_arn": terraform_output(WWW_SHARED_DIR, "bucket_arn"),
    }
