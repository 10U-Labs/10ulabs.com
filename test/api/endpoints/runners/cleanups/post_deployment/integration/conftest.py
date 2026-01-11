"""Shared fixtures for runners cleanup post-deployment integration tests."""
import pytest


@pytest.fixture
def function_name(res_prefix: str) -> str:
    """Provide the Lambda function name."""
    return f"{res_prefix}RunnersCleanups"


@pytest.fixture
def queue_name(res_prefix: str) -> str:
    """Provide the SQS queue name."""
    return f"{res_prefix}RunnersCleanups"
