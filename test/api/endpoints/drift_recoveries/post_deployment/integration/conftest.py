"""Shared fixtures for drift recoveries post-deployment integration tests."""
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
