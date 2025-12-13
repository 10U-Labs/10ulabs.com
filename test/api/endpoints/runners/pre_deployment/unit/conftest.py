"""Shared fixtures for runners pre-deployment unit tests."""
import importlib.util
import json
import re
from pathlib import Path
from typing import Any
from types import ModuleType
from unittest.mock import MagicMock, Mock, patch

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
from module_utils import reset_module_state

# Re-export for backward compatibility with existing tests
__all__ = [
    'parse_response_body',
    'assert_response_status',
    'assert_json_content_type',
    'assert_cors_headers',
    'create_client_error',
    'create_multi_client_mock',
    'create_boto_client_mock',
    'create_mock_lambda_list_mappings_error',
    'create_mock_lambda_put_concurrency_error',
    'create_mock_sns_publish_error',
    'create_mock_lambda_with_mappings',
    'create_mock_lambda_with_disabled_mappings',
    'create_mock_lambda_delete_concurrency_error',
    'reset_module_state',
    'create_mock_dynamodb_for_reset',
]


def create_mock_dynamodb_for_reset():
    """Create a mock DynamoDB client configured for reset state testing."""
    mock_db_client = MagicMock()
    return mock_db_client


def create_circuit_breaker_status_mocks(
    db_state='closed', sqs_state='Enabled', concurrency=None
):
    """Create mocks for circuit breaker status checks."""
    mock_db = MagicMock()
    mock_db.get_item.return_value = {
        'Item': {
            'state': {'S': db_state},
            'last_failure_time': {'N': '0'},
            'recovery_attempts': {'N': '0'}
        }
    }
    mock_lam = MagicMock()
    mock_lam.list_event_source_mappings.return_value = {
        'EventSourceMappings': [{'State': sqs_state}] if sqs_state else []
    }
    if concurrency is None:
        mock_lam.get_function_concurrency.return_value = {}
    else:
        mock_lam.get_function_concurrency.return_value = {
            'ReservedConcurrentExecutions': concurrency
        }
    return mock_db, mock_lam


@pytest.fixture
def cb_status_mock_factory():
    """Factory fixture for creating circuit breaker status check mocks."""
    return create_circuit_breaker_status_mocks


@pytest.fixture
def cb_dynamodb_reset_mock():
    """Fixture providing patched boto3 client returning DynamoDB mock for reset."""
    with patch.dict('os.environ', {}):
        with patch('boto3.client') as mock_boto:
            mock_db = MagicMock()
            mock_boto.return_value = mock_db
            yield mock_db


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
RUNNERS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "runners"


@pytest.fixture
def runners_src_path() -> Path:
    """Provide path to runners source directory."""
    return RUNNERS_SRC_PATH


def get_lambda_path(filename: str) -> Path:
    """Get path to a lambda file in the runners endpoint."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent.parent
    return base / "src" / "api" / "endpoints" / "runners" / "lambdas" / filename


def load_handler_module(relative_path: str, module_name: str) -> ModuleType:
    """Load a handler module dynamically from relative path."""
    base_path = Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "api"
    handler_path = base_path / relative_path
    spec = importlib.util.spec_from_file_location(module_name, handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_lambda_module(filename: str, module_name: str) -> ModuleType:
    """Load a lambda module dynamically for testing."""
    handler_path = get_lambda_path(filename)
    spec = importlib.util.spec_from_file_location(module_name, handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_lambda_response_payload(response: Any) -> Any:
    """Parse Lambda invocation response payload."""
    return json.loads(response['Payload'].read())


@pytest.fixture
def webhook_router(config):
    """Provide webhook router module with mocked environment."""
    env_vars = {
        'API_KEY_PARAMETER_NAME': config['ssm_parameter_name_for_api_key'],
        'WEBHOOK_SECRET_NAME': config['ssm_parameter_name_for_webhook_secret'],
        'API_BASE_URL': f"https://{config['api_fqdn']}/{config['api_version']}",
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("webhook_router.py", "webhook_router")
        if hasattr(module, '_clients'):
            clients = {'ssm': None, 'dynamodb': None, 'sqs': None, 'cloudwatch': None}
            setattr(module, '_clients', clients)
        if hasattr(module, '_webhook_secret_cache'):
            setattr(module, '_webhook_secret_cache', {'value': None})
        if hasattr(module, '_api_key_cache'):
            setattr(module, '_api_key_cache', {'value': None})
        if hasattr(module, '_circuit_breaker_state'):
            state = {'failures': 0, 'last_failure_time': 0.0, 'state': 'closed'}
            setattr(module, '_circuit_breaker_state', state)
        yield module


@pytest.fixture
def circuit_breaker_remediation(config):
    """Provide circuit breaker remediation module."""
    env_vars = {
        'AWS_REGION': config['aws_region']
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("circuit_breaker_remediation.py", "circuit_breaker_remediation")
        yield module


@pytest.fixture
def circuit_breaker_reset(config):
    """Provide circuit breaker reset module."""
    env_vars = {
        'AWS_REGION': config['aws_region'],
        'WEBHOOK_FUNCTION_NAME': 'test-webhook-function',
        'STATE_TABLE_NAME': 'test-state-table'
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("circuit_breaker_reset.py", "circuit_breaker_reset")
        yield module


@pytest.fixture
def dlq_reprocessor(config):
    """Provide DLQ reprocessor module."""
    env_vars = {
        'AWS_REGION': config['aws_region']
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("dlq_reprocessor.py", "dlq_reprocessor")
        yield module


@pytest.fixture
def circuit_breaker_recovery(config):
    """Provide circuit breaker recovery module."""
    env_vars = {
        'AWS_REGION': config['aws_region']
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("circuit_breaker_recovery.py", "circuit_breaker_recovery")
        yield module


@pytest.fixture
def drift_recovery(config):
    """Provide drift recovery module."""
    env_vars = {
        'AWS_REGION': config['aws_region'],
        'GITHUB_REPO': config['github_repo'],
        'GITHUB_TOKEN_PARAMETER_NAME': config['ssm_parameter_name_for_github_pat'],
        'SNS_TOPIC_ARN': f'arn:aws:sns:{TEST_AWS_REGION}:123456789012:test-topic',
        'MANAGED_VPC_ID': 'vpc-managed123'
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("drift_recovery.py", "drift_recovery")
        if hasattr(module, '_clients'):
            setattr(module, '_clients', {})
        yield module


@pytest.fixture
def spot_interruption_handler(config):
    """Provide spot interruption handler module."""
    env_vars = {
        'AWS_REGION': config['aws_region'],
        'ECS_CLUSTER': config['cluster_name'],
        'GITHUB_REPO': config['github_repo'],
        'GITHUB_TOKEN_SECRET_NAME': config['ssm_parameter_name_for_github_pat'],
        'API_BASE_URL': f"https://{config['api_fqdn']}",
        'API_KEY': 'test-api-key',
        'WORKFLOW_RUNNERS_TABLE': 'test-workflow-runners'
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("spot_interruption_handler.py", "spot_interruption_handler")
        if hasattr(module, '_clients'):
            setattr(module, '_clients', {})
        yield module


@pytest.fixture
def stale_runner_cleanup(config):
    """Provide stale runner cleanup module."""
    env_vars = {
        'AWS_REGION': config['aws_region'],
        'ECS_CLUSTER': config['cluster_name'],
        'GITHUB_REPO': config['github_repo'],
        'GITHUB_TOKEN_SECRET_NAME': config['ssm_parameter_name_for_github_pat'],
        'WORKFLOW_RUNNERS_TABLE': 'test-workflow-runners',
        'EC2_MANAGED_BY_TAG': 'ec2-runner-api'
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("stale_runner_cleanup.py", "stale_runner_cleanup")
        if hasattr(module, '_clients'):
            setattr(module, '_clients', {})
        yield module


@pytest.fixture
def mock_sqs():
    """Provide mocked SQS client."""
    with patch('boto3.client') as mock_boto_client:
        mock_sqs_client = MagicMock()
        mock_boto_client.return_value = mock_sqs_client
        yield mock_sqs_client


@pytest.fixture
def mock_dynamodb():
    """Provide mocked DynamoDB client."""
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb_client = MagicMock()
        mock_boto_client.return_value = mock_dynamodb_client
        yield mock_dynamodb_client


@pytest.fixture
def mock_ssm():
    """Provide mocked SSM client."""
    with patch('boto3.client') as mock_boto_client:
        mock_ssm_client = MagicMock()
        mock_ssm_client.get_parameter.return_value = {
            'Parameter': {'Value': 'test-token'}
        }
        mock_boto_client.return_value = mock_ssm_client
        yield mock_ssm_client


@pytest.fixture
def mock_cloudwatch():
    """Provide mocked CloudWatch client."""
    with patch('boto3.client') as mock_boto_client:
        mock_cw_client = MagicMock()
        mock_boto_client.return_value = mock_cw_client
        yield mock_cw_client


@pytest.fixture
def workflow_job_event_factory():
    """Factory for creating workflow_job webhook events."""
    return create_workflow_job_event


@pytest.fixture
def sqs_event_factory():
    """Factory for creating SQS trigger events."""
    return create_sqs_event


@pytest.fixture
def dlq_message_factory():
    """Factory for creating DLQ message events."""
    return create_dlq_message


@pytest.fixture
def circuit_breaker_closed_state():
    """Provide closed circuit breaker state."""
    return create_circuit_breaker_closed_state()


@pytest.fixture
def circuit_breaker_open_state():
    """Provide open circuit breaker state."""
    return create_circuit_breaker_open_state()


@pytest.fixture
def mock_urllib_response_factory():
    """Factory for creating mock urllib responses."""
    return create_mock_urllib_response


def assert_no_hardcoded_env_defaults(lambda_path: Path) -> None:
    """Assert that lambda file has no hardcoded environment defaults."""
    with open(lambda_path, 'r', encoding='utf-8') as f:
        content = f.read()
    os_environ_get_pattern_with_default = r"os\.environ\.get\(['\"][^'\"]+['\"],\s*['\"]"
    matches = re.findall(os_environ_get_pattern_with_default, content)
    assert len(matches) == 0


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


@pytest.fixture
def lambda_context():
    """Provide a mock Lambda context object."""
    return Mock()
