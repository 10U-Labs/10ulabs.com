"""Shared fixtures for drift recoveries unit tests."""
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest

from module_utils import create_lambda_loader
from repo_utils import REPO_ROOT


DRIFT_RECOVERIES_SRC_PATH = (
    REPO_ROOT / "src" / "api" / "endpoints" / "drift_recoveries"
)
DRIFT_RECOVERIES_LAMBDA_PATH = DRIFT_RECOVERIES_SRC_PATH / "lambda"

# Add lambda path to sys.path so modules can be found when patching
if str(DRIFT_RECOVERIES_LAMBDA_PATH) not in sys.path:
    sys.path.insert(0, str(DRIFT_RECOVERIES_LAMBDA_PATH))

# Use shared lambda loader for drift recoveries lambda
load_lambda_module = create_lambda_loader(DRIFT_RECOVERIES_LAMBDA_PATH)


@pytest.fixture
def config(shared_config) -> Dict[str, str]:
    """Provide config for unit tests."""
    return {
        'aws_region': shared_config['aws_region'],
        'resource_prefix': shared_config['resource_prefix'],
    }


@pytest.fixture
def lambda_context():
    """Provide a mock Lambda context object."""
    return Mock()


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for Lambda handler."""
    return {
        'GITHUB_REPO': '10U-Labs-LLC/10ulabs.com',
        'GITHUB_TOKEN_PARAMETER_NAME': '/10ULabs/GitHubToken',
        'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-2:123456789012:10ULabsAlerts',
        'MANAGED_VPC_ID': 'vpc-12345678',
    }


@pytest.fixture
def handler_module(config, mock_env_vars):
    """Provide the handler module with mocked environment."""
    with patch.dict('os.environ', mock_env_vars):
        module = load_lambda_module("handler.py", "handler")
        yield module


@pytest.fixture
def sample_sqs_event() -> Dict[str, Any]:
    """Provide a sample SQS event with Config compliance change."""
    return {
        'Records': [{
            'messageId': 'test-message-id',
            'body': '''{
                "source": "drift-recovery-trigger",
                "configRuleName": "10ULabs-required-tags",
                "resourceType": "AWS::EC2::SecurityGroup",
                "resourceId": "sg-12345678",
                "awsRegion": "us-east-2"
            }'''
        }]
    }


@pytest.fixture
def sample_direct_event() -> Dict[str, Any]:
    """Provide a sample direct event (no SQS wrapper)."""
    return {
        'source': 'drift-recovery-trigger',
        'configRuleName': '10ULabs-required-tags',
        'resourceType': 'AWS::EC2::Subnet',
        'resourceId': 'subnet-12345678',
        'awsRegion': 'us-east-2',
    }


@pytest.fixture
def mock_ec2_client():
    """Provide a mock EC2 client."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_ssm_client():
    """Provide a mock SSM client."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_sns_client():
    """Provide a mock SNS client."""
    client = MagicMock()
    return client
