"""Pytest fixtures for ECS runner post-deployment integration tests."""
import boto3
import pytest

from ...conftest import ECS_RUNNER_SRC, terraform_output

# Enable layer marker plugin for test ordering
pytest_plugins = ['pytest_layers']


@pytest.fixture(scope="session")
def lambda_role_name():
    """Get the Lambda execution role name from terraform outputs."""
    return terraform_output(ECS_RUNNER_SRC, "lambda_role_name")


@pytest.fixture(scope="session")
def lambda_function_name():
    """Get the Lambda function name from terraform outputs."""
    return terraform_output(ECS_RUNNER_SRC, "lambda_function_name")


@pytest.fixture(scope="session")
def ecs_task_role_name():
    """Get the ECS task role name from terraform outputs."""
    return terraform_output(ECS_RUNNER_SRC, "task_role_name")


@pytest.fixture(scope="session")
def cluster_name():
    """Get the ECS cluster name from terraform outputs."""
    return terraform_output(ECS_RUNNER_SRC, "cluster_name")


@pytest.fixture(scope="session")
def lambda_client(config):
    """Create a Lambda client."""
    return boto3.client("lambda", region_name=config["aws_region"])


@pytest.fixture(scope="session")
def iam_client(config):
    """Create an IAM client."""
    return boto3.client("iam", region_name=config["aws_region"])


@pytest.fixture(scope="session")
def lambda_function(request):
    """Get Lambda function configuration."""
    l_client = request.getfixturevalue("lambda_client")
    l_function_name = request.getfixturevalue("lambda_function_name")
    if not l_function_name:
        pytest.fail("Lambda function name not configured")
    response = l_client.get_function(FunctionName=l_function_name)
    return response["Configuration"]


@pytest.fixture(scope="session")
def task_definition(ecs_client):
    """Get the latest ECS task definition."""
    response = ecs_client.list_task_definitions(
        familyPrefix='github-runner', status='ACTIVE'
    )
    if not response['taskDefinitionArns']:
        return None
    task_def_arn = response['taskDefinitionArns'][-1]
    return ecs_client.describe_task_definition(
        taskDefinition=task_def_arn
    )['taskDefinition']
