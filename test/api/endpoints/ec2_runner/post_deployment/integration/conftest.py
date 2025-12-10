"""Pytest fixtures for EC2 runner integration tests."""
import boto3
import pytest

from ...conftest import EC2_RUNNER_SRC, terraform_output
from ..conftest import (
    api_key_fixture,
    api_url_fixture,
)

api_url = api_url_fixture
api_key = api_key_fixture


@pytest.fixture(scope="session")
def kms_client(aws_region):
    """Create a KMS client."""
    return boto3.client("kms", region_name=aws_region)


@pytest.fixture(scope="session")
def lambda_client(aws_region):
    """Create a Lambda client."""
    return boto3.client("lambda", region_name=aws_region)


@pytest.fixture(scope="session")
def lambda_role_name():
    """Get the Lambda execution role name from terraform outputs."""
    return terraform_output(EC2_RUNNER_SRC, "lambda_role_name")


@pytest.fixture(scope="session")
def lambda_function_name():
    """Get the Lambda function name from terraform outputs."""
    return terraform_output(EC2_RUNNER_SRC, "lambda_function_name")


@pytest.fixture(scope="session")
def lambda_role_arn(shared_config):
    """Get the full ARN for the Lambda execution role."""
    account_id = shared_config.get("aws_account_id", "")
    role_name = terraform_output(EC2_RUNNER_SRC, "lambda_role_name")
    return f"arn:aws:iam::{account_id}:role/{role_name}"
