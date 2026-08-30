from unittest.mock import Mock

import boto3
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
