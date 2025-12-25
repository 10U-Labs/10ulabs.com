"""Pytest fixtures for pre-deployment unit tests."""
import json
from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest

from repo_utils import REPO_ROOT
from test_fixtures.unit import (
    create_lambda_loader,
    create_workflow_job_event,
    create_sqs_event,
)
from event_factories import create_ecs_runner_post_event

BACKEND_LAMBDAS_PATH = REPO_ROOT / "src" / "api" / "backend" / "lambdas"

# Create lambda loader for backend lambdas
load_lambda_module = create_lambda_loader(BACKEND_LAMBDAS_PATH)


@pytest.fixture
def openapi_spec() -> Dict[str, Any]:
    """Load and return the OpenAPI specification."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent
    openapi_path = base / "src" / "www" / "api" / "openapi.json"
    with open(openapi_path, 'r', encoding='utf-8') as f:
        return json.load(f)


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
    return create_ecs_runner_post_event


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


# assert_no_hardcoded_env_defaults imported from test_fixtures.unit
# TEST_CONSTANTS imported from test_fixtures.unit
# ENV_VAR_PRESETS imported from test_fixtures.unit
