"""Shared fixtures for EC2 spot interruptions post-deployment integration tests."""
import pytest


@pytest.fixture
def function_name(request) -> str:
    """Provide the Lambda function name."""
    prefix = request.getfixturevalue('res_prefix')
    return f"{prefix}EC2SpotInterruptions"


@pytest.fixture
def queue_name(request) -> str:
    """Provide the SQS queue name."""
    prefix = request.getfixturevalue('res_prefix')
    return f"{prefix}EC2SpotInterruptions"
