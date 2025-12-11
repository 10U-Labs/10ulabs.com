"""Pytest fixtures for ECS runner post-deployment integration tests."""
import pytest

from ...conftest import ECS_RUNNER_SRC, terraform_output


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
