"""Shared fixtures for ECS task stops post-deployment integration tests."""
from typing import Dict

import pytest


@pytest.fixture
def config(shared_config) -> Dict[str, str]:
    """Provide config for integration tests."""
    return {
        'aws_region': shared_config['aws_region'],
        'resource_prefix': shared_config['resource_prefix'],
    }


@pytest.fixture
def resource_prefix(config) -> str:
    """Provide the resource prefix for AWS resources."""
    return config.get('resource_prefix', '10ULabs')


@pytest.fixture
def function_name(resource_prefix: str) -> str:
    """Provide the Lambda function name."""
    return f"{resource_prefix}EcsTaskStops"


@pytest.fixture
def queue_name(resource_prefix: str) -> str:
    """Provide the SQS queue name."""
    return f"{resource_prefix}EcsTaskStops"
