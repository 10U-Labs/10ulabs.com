"""Shared fixtures for EC2 spot interruptions post-deployment integration tests."""
from typing import Dict

import pytest


@pytest.fixture
def cfg(shared_config) -> Dict[str, str]:
    """Provide config for integration tests."""
    return {
        'aws_region': shared_config['aws_region'],
        'resource_prefix': shared_config['resource_prefix'],
    }


@pytest.fixture
def res_prefix(request) -> str:
    """Provide the resource prefix for AWS resources."""
    config = request.getfixturevalue('cfg')
    return config.get('resource_prefix', '10ULabs')


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
