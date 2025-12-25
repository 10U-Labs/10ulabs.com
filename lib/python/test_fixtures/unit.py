"""Shared fixtures and utilities for unit testing Lambda handlers.

This module provides common test utilities, mock fixtures, and constants
that are shared across multiple Lambda unit test suites.
"""
import json
import re
from pathlib import Path
from types import ModuleType
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
    create_workflow_job_event,
    create_sqs_event,
    create_dlq_message,
    create_circuit_breaker_closed_state,
    create_circuit_breaker_open_state,
)
from urllib_mocks import create_mock_urllib_response
from module_utils import reset_module_state, create_lambda_loader
from repo_utils import REPO_ROOT

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
    'create_workflow_job_event',
    'create_sqs_event',
    'create_dlq_message',
    'create_circuit_breaker_closed_state',
    'create_circuit_breaker_open_state',
    # urllib_mocks
    'create_mock_urllib_response',
    # module_utils
    'reset_module_state',
    # Constants
    'TEST_AWS_REGION',
    'TEST_CONSTANTS',
    'ENV_VAR_PRESETS',
    # Helper functions
    'load_handler_module',
    'parse_lambda_response_payload',
    'assert_no_hardcoded_env_defaults',
    'create_lambda_loader',
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
    'webhook_router': {
        'AWS_REGION': TEST_AWS_REGION,
        'API_KEY_PARAMETER_NAME': 'test-api-key-param',
        'WEBHOOK_SECRET_NAME': 'test-webhook-secret',
        'API_BASE_URL': 'https://api.test.com/v1',
        'IDEMPOTENCY_TABLE_NAME': 'test-table',
        'JOB_QUEUE_URL': f'https://sqs.{TEST_AWS_REGION}.amazonaws.com/123456789012/test-queue',
    },
}


def load_handler_module(relative_path: str, module_name: str) -> ModuleType:
    """Load a handler module dynamically from relative path.

    Args:
        relative_path: Path relative to src/api/ directory
        module_name: Name for the loaded module

    Returns:
        Loaded Python module
    """
    base_path = REPO_ROOT / "src" / "api"
    # Get the directory containing the handler
    handler_dir = base_path / Path(relative_path).parent
    filename = Path(relative_path).name
    loader = create_lambda_loader(handler_dir)
    return loader(filename, module_name)


def parse_lambda_response_payload(response: Any) -> Any:
    """Parse the payload from a Lambda invocation response.

    Args:
        response: Lambda invocation response dict with 'Payload' key

    Returns:
        Parsed JSON from the response payload
    """
    return json.loads(response['Payload'].read())


def assert_no_hardcoded_env_defaults(lambda_path: Path) -> None:
    """Assert Lambda has no hardcoded environment variable defaults.

    Args:
        lambda_path: Path to the Lambda handler file

    Raises:
        AssertionError: If hardcoded defaults are found
    """
    with open(lambda_path, 'r', encoding='utf-8') as f:
        content = f.read()
    os_environ_get_pattern_with_default = r"os\.environ\.get\(['\"][^'\"]+['\"],\s*['\"]"
    matches = re.findall(os_environ_get_pattern_with_default, content)
    assert len(matches) == 0


# Standalone fixtures for pytest_plugins loading
@pytest.fixture
def mock_sqs():
    """Provide a mock SQS client."""
    with patch('boto3.client') as mock_boto_client:
        mock_sqs_client = MagicMock()
        mock_boto_client.return_value = mock_sqs_client
        yield mock_sqs_client


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
def mock_cloudwatch():
    """Provide a mock CloudWatch client."""
    with patch('boto3.client') as mock_boto_client:
        mock_cw_client = MagicMock()
        mock_boto_client.return_value = mock_cw_client
        yield mock_cw_client


@pytest.fixture
def workflow_job_event_factory():
    """Factory for creating workflow job events."""
    return create_workflow_job_event


@pytest.fixture
def sqs_event_factory():
    """Factory for creating SQS events."""
    return create_sqs_event


@pytest.fixture
def dlq_message_factory():
    """Factory for creating DLQ messages."""
    return create_dlq_message


@pytest.fixture
def circuit_breaker_closed_state():
    """Provide a closed circuit breaker state."""
    return create_circuit_breaker_closed_state()


@pytest.fixture
def circuit_breaker_open_state():
    """Provide an open circuit breaker state."""
    return create_circuit_breaker_open_state()


@pytest.fixture
def mock_urllib_response_factory():
    """Factory for creating mock urllib responses."""
    return create_mock_urllib_response
