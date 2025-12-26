"""Pytest fixtures for ECS runner post-deployment integration tests."""
import pytest

from test_fixtures.aws import get_log_group_info
from test_fixtures.terraform import terraform_output

from ...conftest import ECS_RUNNER_SRC

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


@pytest.fixture(scope="module")
def lambda_log_group(request, logs_client):
    """Get the Lambda handler log group info from CloudWatch."""
    function_name = request.getfixturevalue("lambda_function_name")
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(scope="module")
def ecs_log_group(logs_client):
    """Get the ECS task log group info from CloudWatch."""
    return get_log_group_info(logs_client, "/ecs/github-runner")


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
