"""Pytest fixtures for runners pre-deployment integration tests.

Runners Pre-Deployment Layers:
- Layer 1: Contracts - Cross-file compatibility (Lambda handler, Terraform refs)
- Layer 2: Authentication - AWS credentials valid
- Layer 3: Authorization - Permission to inspect prerequisites
- Layer 4: State - Terraform state matches AWS reality
- Layer 5: Existence - Prerequisite resources exist (API Gateway, IAM roles)
- Layer 6: Configuration - Prerequisites configured correctly
- Layer 7: Capability - Can perform required operations
"""
from pathlib import Path

import boto3
import pytest
from repo_utils import REPO_ROOT
from terraform_config import TEST_AWS_REGION
from test_fixtures.terraform import terraform_init, terraform_output

pytest_plugins = ['pytest_layers']


RUNNERS_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "runners"
BOOTSTRAP_DIR = REPO_ROOT / "src" / "bootstrap"
API_COMMON_ROUTING_DIR = REPO_ROOT / "src" / "api" / "common" / "routing"


def _get_bootstrap_outputs() -> dict:
    """Get bootstrap terraform outputs."""
    if not terraform_init(BOOTSTRAP_DIR):
        return {}
    return {
        "state_bucket_arn": terraform_output(
            BOOTSTRAP_DIR, "arn_for_state_bucket"
        ),
        "github_actions_role_arn": terraform_output(
            BOOTSTRAP_DIR, "arn_for_github_actions_role"
        ),
        "github_actions_role_name": terraform_output(
            BOOTSTRAP_DIR, "name_for_github_actions_role"
        ),
    }


def _get_api_common_routing_outputs() -> dict:
    """Get api_common_routing terraform outputs."""
    if not terraform_init(API_COMMON_ROUTING_DIR):
        return {}
    return {
        "api_gateway_id": terraform_output(
            API_COMMON_ROUTING_DIR, "api_gateway_id"
        ),
        "api_gateway_root_resource_id": terraform_output(
            API_COMMON_ROUTING_DIR, "api_gateway_root_resource_id"
        ),
    }


@pytest.fixture(scope="session", name="runners_dir")
def runners_dir_fixture() -> Path:
    """Get the runners source directory."""
    return RUNNERS_DIR


@pytest.fixture(scope="session", name="lambda_dir")
def lambda_dir_fixture() -> Path:
    """Get the runners lambda directory."""
    return RUNNERS_DIR / "lambda"


@pytest.fixture(scope="session", name="aws_region")
def aws_region_fixture():
    """Provide the AWS region."""
    return TEST_AWS_REGION


@pytest.fixture(scope="session", name="sts_client")
def sts_client_fixture():
    """Create an STS client."""
    return boto3.client("sts", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session", name="iam_client")
def iam_client_fixture():
    """Create an IAM client."""
    return boto3.client("iam", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session", name="s3_client")
def s3_client_fixture():
    """Create an S3 client."""
    return boto3.client("s3", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session", name="lambda_client")
def lambda_client_fixture():
    """Create a Lambda client."""
    return boto3.client("lambda", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session", name="apigateway_client")
def apigateway_client_fixture():
    """Create an API Gateway client."""
    return boto3.client("apigateway", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session", name="sqs_client")
def sqs_client_fixture():
    """Create an SQS client."""
    return boto3.client("sqs", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session", name="bootstrap_outputs")
def bootstrap_outputs_fixture():
    """Get bootstrap terraform outputs."""
    outputs = _get_bootstrap_outputs()
    if not outputs:
        pytest.skip("Terraform init failed for bootstrap")
    return outputs


@pytest.fixture(scope="session", name="api_common_routing_outputs")
def api_common_routing_outputs_fixture():
    """Get api_common_routing terraform outputs."""
    outputs = _get_api_common_routing_outputs()
    if not outputs:
        pytest.skip("Terraform init failed for api_common_routing")
    return outputs


@pytest.fixture(scope="session", name="state_bucket_name")
def state_bucket_name_fixture(bootstrap_outputs):
    """Extract state bucket name from ARN."""
    arn = bootstrap_outputs.get("state_bucket_arn", "")
    if not arn:
        pytest.skip("state_bucket_arn not found in bootstrap outputs")
    return arn.split(":")[-1]


@pytest.fixture(scope="session", name="github_actions_role_arn")
def github_actions_role_arn_fixture(bootstrap_outputs):
    """Get GitHub Actions role ARN."""
    arn = bootstrap_outputs.get("github_actions_role_arn", "")
    if not arn:
        pytest.skip("github_actions_role_arn not found in bootstrap outputs")
    return arn


@pytest.fixture(scope="session", name="github_actions_role_name")
def github_actions_role_name_fixture(bootstrap_outputs):
    """Get GitHub Actions role name."""
    name = bootstrap_outputs.get("github_actions_role_name", "")
    if not name:
        pytest.skip("github_actions_role_name not found in bootstrap outputs")
    return name


@pytest.fixture(scope="session", name="api_gateway_id")
def api_gateway_id_fixture(api_common_routing_outputs):
    """Get API Gateway ID."""
    api_id = api_common_routing_outputs.get("api_gateway_id", "")
    if not api_id:
        pytest.skip("api_gateway_id not found in api_common_routing outputs")
    return api_id


@pytest.fixture(scope="session", name="current_identity")
def current_identity_fixture(sts_client):
    """Get the current AWS identity."""
    return sts_client.get_caller_identity()


@pytest.fixture(scope="session", name="handler_content")
def handler_content_fixture(lambda_dir: Path) -> str:
    """Read the Lambda handler content."""
    handler_path = lambda_dir / "handler.py"
    if not handler_path.exists():
        pytest.skip(f"handler.py not found at {handler_path}")
    return handler_path.read_text()


@pytest.fixture(scope="session", name="lambda_tf_content")
def lambda_tf_content_fixture(runners_dir: Path) -> str:
    """Read the lambda.tf content."""
    lambda_tf_path = runners_dir / "lambda.tf"
    if not lambda_tf_path.exists():
        pytest.skip(f"lambda.tf not found at {lambda_tf_path}")
    return lambda_tf_path.read_text()
