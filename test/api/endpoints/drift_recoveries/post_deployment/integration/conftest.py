"""Shared fixtures for drift recoveries post-deployment integration tests."""
import boto3
import pytest


@pytest.fixture
def function_name(request) -> str:
    """Provide the Lambda function name."""
    prefix = request.getfixturevalue('res_prefix')
    return f"{prefix}DriftRecoveries"


@pytest.fixture
def queue_name(request) -> str:
    """Provide the SQS queue name."""
    prefix = request.getfixturevalue('res_prefix')
    return f"{prefix}DriftRecoveries"


@pytest.fixture(scope="session")
def sqs_client(request):
    """Create an SQS client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("sqs", region_name=region)


@pytest.fixture(scope="session")
def sns_client(request):
    """Create an SNS client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("sns", region_name=region)


@pytest.fixture(scope="session")
def config_client(request):
    """Create an AWS Config client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("config", region_name=region)
