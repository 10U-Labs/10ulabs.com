"""Pytest fixtures for pre-deployment unit tests."""
import importlib.util
import json
import re
from pathlib import Path
from typing import Any, Dict
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
import yaml

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
]


def get_lambda_path(filename: str) -> Path:
    """Get the path to a Lambda handler file."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent
    return base / "src" / "api" / "backend" / "lambdas" / filename


def load_handler_module(relative_path: str, module_name: str) -> ModuleType:
    """Load a handler module from the API source directory."""
    base_path = Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "api"
    handler_path = base_path / relative_path
    spec = importlib.util.spec_from_file_location(module_name, handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_lambda_module(filename: str, module_name: str) -> ModuleType:
    """Load a Lambda module by filename."""
    handler_path = get_lambda_path(filename)
    spec = importlib.util.spec_from_file_location(module_name, handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_lambda_response_payload(response: Any) -> Any:
    """Parse the payload from a Lambda invocation response."""
    return json.loads(response['Payload'].read())


@pytest.fixture
def openapi_spec() -> Dict[str, Any]:
    """Load and return the OpenAPI specification."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent
    openapi_path = base / "src" / "www" / "api" / "openapi.yml"
    with open(openapi_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture
def catchall_handler():
    """Load the catchall Lambda handler module."""
    return load_lambda_module("catchall.py", "catchall_handler")


@pytest.fixture
def webhook_router(config):
    """Load the webhook router Lambda with test environment."""
    env_vars = {
        'API_KEY_PARAMETER_NAME': config['ssm_parameter_name_for_api_key'],
        'WEBHOOK_SECRET_NAME': config['ssm_parameter_name_for_webhook_secret'],
        'API_BASE_URL': f"https://{config['api_fqdn']}/{config['api_version']}",
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("webhook_router.py", "webhook_router")
        if hasattr(module, '_clients'):
            setattr(module, '_clients', {
                'ssm': None, 'dynamodb': None, 'sqs': None, 'cloudwatch': None
            })
        if hasattr(module, '_webhook_secret_cache'):
            setattr(module, '_webhook_secret_cache', {'value': None})
        if hasattr(module, '_api_key_cache'):
            setattr(module, '_api_key_cache', {'value': None})
        if hasattr(module, '_circuit_breaker_state'):
            setattr(module, '_circuit_breaker_state', {
                'failures': 0, 'last_failure_time': 0.0, 'state': 'closed'
            })
        yield module


@pytest.fixture
def circuit_breaker_remediation(config):
    """Load circuit breaker remediation Lambda with test environment."""
    env_vars = {
        'AWS_REGION': config['aws_region']
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module(
            "circuit_breaker_remediation.py", "circuit_breaker_remediation"
        )
        yield module


@pytest.fixture
def dlq_reprocessor(config):
    """Load DLQ reprocessor Lambda with test environment."""
    env_vars = {
        'AWS_REGION': config['aws_region']
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("dlq_reprocessor.py", "dlq_reprocessor")
        yield module


@pytest.fixture
def circuit_breaker_recovery(config):
    """Load circuit breaker recovery Lambda with test environment."""
    env_vars = {
        'AWS_REGION': config['aws_region']
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module(
            "circuit_breaker_recovery.py", "circuit_breaker_recovery"
        )
        yield module


@pytest.fixture
def drift_recovery(config):
    """Load drift recovery Lambda with test environment."""
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
    """Load spot interruption handler Lambda with test environment."""
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
        module = load_lambda_module(
            "spot_interruption_handler.py", "spot_interruption_handler"
        )
        if hasattr(module, '_clients'):
            setattr(module, '_clients', {})
        yield module


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
def catchall_unknown_event():
    """Create an event for an unknown path."""
    return {'path': '/unknown', 'httpMethod': 'GET'}


@pytest.fixture
def ecs_runner_post_event_factory():
    """Factory for creating ECS runner POST events."""
    def _create_event(job_id=123, job_labels=None, github_repo='test/repo'):
        if job_labels is None:
            job_labels = ['fargate', 'self-hosted']
        return {
            'path': '/v1/ecs-runner',
            'httpMethod': 'POST',
            'body': json.dumps({
                'job_id': job_id,
                'job_labels': job_labels,
                'github_repo': github_repo
            })
        }
    return _create_event


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


def assert_no_hardcoded_env_defaults(lambda_path: Path) -> None:
    """Assert Lambda has no hardcoded environment variable defaults."""
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
