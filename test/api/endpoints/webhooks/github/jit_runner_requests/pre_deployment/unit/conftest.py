"""Shared fixtures for runners pre-deployment unit tests."""
import importlib.util
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, Mock, patch

import pytest

from module_utils import create_lambda_loader
from repo_utils import REPO_ROOT

# Re-exports for test files
__all__ = [
    'circuit_breaker_utils',
    'get_lambda_path',
    'load_lambda_module',
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


RUNNERS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "webhooks" / "github" / "jit_runner_requests"
RUNNERS_LAMBDAS_PATH = RUNNERS_SRC_PATH / "lambdas"


def get_lambda_path(filename: str) -> Path:
    """Get the full path to a lambda file."""
    return RUNNERS_LAMBDAS_PATH / filename


@pytest.fixture
def runners_src_path() -> Path:
    """Provide path to runners source directory."""
    return RUNNERS_SRC_PATH


# Use shared lambda loader for runners lambdas
load_lambda_module = create_lambda_loader(RUNNERS_LAMBDAS_PATH)


def load_common_module(filename: str, module_name: str) -> ModuleType:
    """Load a common module from lambdas/common directory for testing."""
    common_path = RUNNERS_SRC_PATH / "lambdas" / "common" / filename
    spec = importlib.util.spec_from_file_location(module_name, common_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {module_name} from {common_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Pre-loaded common modules for test imports
circuit_breaker_utils = load_common_module(
    "circuit_breaker_utils.py", "circuit_breaker_utils"
)


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
def lambda_context():
    """Provide a mock Lambda context object."""
    return Mock()


@pytest.fixture
def health_check_module():
    """Load health_check module for testing."""
    return load_lambda_module("health_check.py", "health_check")
