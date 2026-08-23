"""Shared fixtures and utilities for unit testing Lambda handlers.

This module provides common test utilities, mock fixtures, and constants
that are shared across multiple Lambda unit test suites.
"""
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from terraform_config import TEST_AWS_REGION
from lambda_response import (
    parse_response_body,
    assert_response_status,
    assert_json_content_type,
    assert_cors_headers,
)
from boto_mocks import (
    create_client_error,
    create_multi_client_mock,
    create_boto_client_mock,
    create_mock_lambda_list_mappings_error,
    create_mock_lambda_put_concurrency_error,
    create_mock_sns_publish_error,
    create_mock_lambda_with_mappings,
    create_mock_lambda_with_disabled_mappings,
    create_mock_lambda_delete_concurrency_error,
)
from event_factories import (
    create_sqs_event,
    create_dlq_message,
)
from urllib_mocks import create_mock_urllib_response
from module_utils import reset_module_state, create_lambda_loader

# Re-export for backward compatibility with existing tests
__all__ = [
    # lambda_response
    'parse_response_body',
    'assert_response_status',
    'assert_json_content_type',
    'assert_cors_headers',
    # boto_mocks
    'create_client_error',
    'create_multi_client_mock',
    'create_boto_client_mock',
    'create_mock_lambda_list_mappings_error',
    'create_mock_lambda_put_concurrency_error',
    'create_mock_sns_publish_error',
    'create_mock_lambda_with_mappings',
    'create_mock_lambda_with_disabled_mappings',
    'create_mock_lambda_delete_concurrency_error',
    # event_factories
    'create_sqs_event',
    'create_dlq_message',
    # urllib_mocks
    'create_mock_urllib_response',
    # module_utils
    'reset_module_state',
    # Constants
    'TEST_AWS_REGION',
    'TEST_CONSTANTS',
    'ENV_VAR_PRESETS',
    # Helper functions
    'create_lambda_loader',
    'create_mock_dynamodb_client',
]


# Standard test constants used across unit tests
TEST_CONSTANTS = {
    'queue_url': f'https://sqs.{TEST_AWS_REGION}.amazonaws.com/123456789012/test-queue',
    'dynamodb_table': 'test-table',
    'lambda_function': 'test-function',
    'instance_id': 'i-test123',
    'instance_id_2': 'i-123',
    'instance_id_3': 'i-456',
    'ami_id': 'ami-test123',
    'ami_id_2': 'ami-123',
    'ecr_digest': 'sha256:test',
    'ecr_digest_2': 'sha256:abc123',
    'task_arn': 'test-task',
    'task_arn_full': f'arn:aws:ecs:{TEST_AWS_REGION}:123456789012:task/test',
    'test_timestamp': '2024-01-01T00:00:00',
    'aws_account_id': '123456789012',
    'aws_region': TEST_AWS_REGION,
}


# Environment variable presets for different Lambda types
ENV_VAR_PRESETS = {
    'base': {
        'AWS_REGION': TEST_AWS_REGION,
    },
}


def create_mock_dynamodb_client(method_name: str, return_value: Any = None) -> MagicMock:
    """Create a mock DynamoDB client with a specified method returning a value.

    Args:
        method_name: The DynamoDB method to mock (e.g., 'batch_write_item').
        return_value: The value to return from the method. Defaults to {}.

    Returns:
        A mock DynamoDB client.
    """
    if return_value is None:
        return_value = {}
    mock_client = MagicMock()
    getattr(mock_client, method_name).return_value = return_value
    return mock_client


@pytest.fixture
def mock_dynamodb():
    """Provide a mock DynamoDB client."""
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb_client = MagicMock()
        mock_boto_client.return_value = mock_dynamodb_client
        yield mock_dynamodb_client


@pytest.fixture
def mock_ssm():
    """Provide a mock SSM client with test parameter."""
    with patch('boto3.client') as mock_boto_client:
        mock_ssm_client = MagicMock()
        mock_ssm_client.get_parameter.return_value = {
            'Parameter': {'Value': 'test-token'}
        }
        mock_boto_client.return_value = mock_ssm_client
        yield mock_ssm_client


@pytest.fixture
def sqs_event_factory():
    """Factory for creating SQS events."""
    return create_sqs_event


@pytest.fixture
def dlq_message_factory():
    """Factory for creating DLQ messages."""
    return create_dlq_message


@pytest.fixture
def mock_urllib_response_factory():
    """Factory for creating mock urllib responses."""
    return create_mock_urllib_response
