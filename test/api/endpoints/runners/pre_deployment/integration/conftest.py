"""Pytest fixtures for pre-deployment integration tests.

Common fixtures (shared_config, aws_region, ecs_runner_outputs,
ecs_runner_terraform_initialized) are inherited from parent conftest files.
"""
from test.api.conftest import REPO_ROOT, terraform_init, terraform_output

import boto3
import pytest


EC2_RUNNER_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "ec2_runner"


@pytest.fixture(scope="session")
def config(shared_config):
    """Provide config for integration tests.

    Shadows parent config fixture with simpler structure for integration tests.
    """
    return {
        'resource_prefix': shared_config.get('resource_prefix', 'TenULabs'),
        'aws_region': shared_config.get('aws_region', 'us-east-2'),
    }


@pytest.fixture(scope="session")
def sqs_client(aws_region):
    """Create an SQS client."""
    return boto3.client("sqs", region_name=aws_region)


@pytest.fixture(scope="session")
def dynamodb_client(aws_region):
    """Create a session-scoped DynamoDB client for integration tests."""
    return boto3.client("dynamodb", region_name=aws_region)


@pytest.fixture(scope="session")
def ec2_runner_terraform_initialized():
    """Initialize terraform for ec2_runner state access."""
    return terraform_init(EC2_RUNNER_DIR)


@pytest.fixture(scope="session")
def ec2_runner_outputs(request):
    """Get ec2_runner terraform outputs."""
    if not request.getfixturevalue("ec2_runner_terraform_initialized"):
        pytest.skip("Terraform init failed for ec2_runner")
    return {
        "lambda_function_arn": terraform_output(
            EC2_RUNNER_DIR, "lambda_function_arn"
        ),
        "lambda_function_name": terraform_output(
            EC2_RUNNER_DIR, "lambda_function_name"
        ),
        "lambda_invoke_arn": terraform_output(
            EC2_RUNNER_DIR, "lambda_invoke_arn"
        ),
        "ec2_instance_profile_name": terraform_output(
            EC2_RUNNER_DIR, "ec2_instance_profile_name"
        ),
        "ec2_runner_role_arn": terraform_output(
            EC2_RUNNER_DIR, "ec2_runner_role_arn"
        ),
    }
