"""Fixtures for image_for_ecs_runners endpoint pre-deployment integration tests."""
from test.api.endpoints.image_for_ecs_runners.conftest import (
    get_aws_region,
    get_ecr_repository,
)

import boto3
import pytest


@pytest.fixture(scope="session")
def aws_region():
    """Provide the AWS region."""
    return get_aws_region()


@pytest.fixture(scope="session")
def ecr_repository_name():
    """Provide the ECR repository name."""
    return get_ecr_repository()


@pytest.fixture(scope="session")
def sts_client(request):
    """Create an STS client for the test session."""
    region = request.getfixturevalue('aws_region')
    return boto3.client("sts", region_name=region)


@pytest.fixture(scope="session")
def ecr_client(request):
    """Create an ECR client for the test session."""
    region = request.getfixturevalue('aws_region')
    return boto3.client("ecr", region_name=region)


@pytest.fixture(scope="session")
def iam_client(request):
    """Create an IAM client for the test session."""
    region = request.getfixturevalue('aws_region')
    return boto3.client("iam", region_name=region)


@pytest.fixture(scope="session")
def ssm_client(request):
    """Create an SSM client for the test session."""
    region = request.getfixturevalue('aws_region')
    return boto3.client("ssm", region_name=region)


@pytest.fixture(scope="session")
def caller_identity(request):
    """Get the current caller identity."""
    client = request.getfixturevalue('sts_client')
    return client.get_caller_identity()
