"""Shared fixtures for retries post-deployment integration tests."""
import pytest


@pytest.fixture
def function_name(res_prefix: str) -> str:
    """Provide the Lambda function name."""
    return f"{res_prefix}GitHubWorkflowsRetries"


@pytest.fixture
def queue_name(res_prefix: str) -> str:
    """Provide the SQS queue name."""
    return f"{res_prefix}GitHubWorkflowsRetries"
