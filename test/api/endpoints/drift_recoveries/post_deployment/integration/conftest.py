"""Shared fixtures for drift recoveries post-deployment integration tests."""
import boto3
import pytest


@pytest.fixture(name="function_name")
def fixture_function_name(request) -> str:
    """Provide the Lambda function name."""
    prefix = request.getfixturevalue('res_prefix')
    return f"{prefix}DriftRecoveries"


@pytest.fixture(name="queue_name")
def fixture_queue_name(request) -> str:
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


@pytest.fixture(name="lambda_role_name")
def fixture_lambda_role_name(lambda_client, function_name):
    """Get the IAM role name for the Lambda function."""
    lambda_config = lambda_client.get_function(FunctionName=function_name)
    role_arn = lambda_config["Configuration"]["Role"]
    return role_arn.split("/")[-1]


@pytest.fixture(name="lambda_inline_policies")
def fixture_lambda_inline_policies(iam_client, lambda_role_name):
    """Get inline policy names for the Lambda role."""
    response = iam_client.list_role_policies(RoleName=lambda_role_name)
    return response.get("PolicyNames", [])
