"""Pytest fixtures for EC2 runner integration tests."""
import boto3
from botocore.exceptions import ClientError
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


@pytest.fixture(scope="session")
def ec2_runner_role_name():
    """Get the EC2 runner IAM role name from terraform outputs."""
    return terraform_output(EC2_RUNNER_SRC, "ec2_runner_role_name")


def get_inline_policy_actions(iam_client, role_name: str, policy_name: str) -> list:
    """Get the list of allowed actions from an inline IAM policy.

    Returns empty list if policy doesn't exist or on error.
    """
    try:
        resp = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        actions = []
        for stmt in resp.get("PolicyDocument", {}).get("Statement", []):
            if stmt.get("Effect") != "Allow":
                continue
            stmt_actions = stmt.get("Action", [])
            if isinstance(stmt_actions, str):
                stmt_actions = [stmt_actions]
            actions.extend(stmt_actions)
        return actions
    except ClientError:
        return []
