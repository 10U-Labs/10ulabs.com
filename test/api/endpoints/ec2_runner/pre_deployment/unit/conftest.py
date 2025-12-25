"""Pytest fixtures for EC2 runner pre-deployment unit tests."""
import json
from typing import Any, Dict
from types import ModuleType
from unittest.mock import MagicMock, Mock, patch

import pytest

from terraform_config import TEST_AWS_REGION
from lambda_response import (
    parse_response_body,
    assert_response_status,
    assert_json_content_type,
)
from boto_mocks import create_client_error, create_multi_client_mock, setup_mock_ec2_vpc_responses
from module_utils import load_module_from_path, reset_module_state

from ...conftest import EC2_RUNNER_SRC

# Re-export for backward compatibility
__all__ = [
    'parse_response_body',
    'assert_response_status',
    'assert_json_content_type',
    'create_client_error',
    'create_multi_client_mock',
]


def load_handler_module() -> ModuleType:
    """Load the EC2 runner handler module dynamically."""
    handler_path = EC2_RUNNER_SRC / "lambda" / "handler.py"
    return load_module_from_path("ec2_runner_handler", handler_path)


@pytest.fixture
def ec2_runner_handler(config: Dict[str, str]) -> Any:
    """Provide an EC2 runner handler module with mocked environment."""
    env_vars = {
        'AWS_REGION': config['aws_region'],
        'EC2_AMI_PURPOSE_TAG': 'Purpose',
        'EC2_AMI_PURPOSE_VALUE': 'GitHub self-hosted EC2 runner',
        'EC2_AMI_STABLE_TAG': 'Stable',
        'EC2_MANAGED_BY_TAG': 'api-ec2-runner',
        'GITHUB_REPO': config['github_repo'],
        'GITHUB_TOKEN_SECRET_NAME': config['ssm_parameter_name_for_github_pat'],
        'EC2_INSTANCE_TYPES': ','.join(config['ec2_instance_types']),
        'API_DOMAIN': config['api_fqdn'],
        'SUBNETS': 'subnet-test1,subnet-test2',
        'SECURITY_GROUPS': 'sg-test',
        'VPC_ID': 'vpc-test',
        'EC2_IAM_INSTANCE_PROFILE': 'test-profile',
        'API_KEY_PARAMETER_NAME': '/test/api-key',
        'WORKFLOW_RUNNERS_TABLE': 'test-workflow-runners'
    }
    with patch.dict('os.environ', env_vars):
        module = load_handler_module()
        reset_module_state(module)
        yield module


@pytest.fixture
def ec2_runner_post_event_factory():
    """Provide a factory for creating EC2 runner POST events."""
    def _create_event(
        job_id=456, job_labels=None, github_repo='test/repo', run_id=None, runner_type='ec2'
    ):
        if job_labels is None:
            job_labels = ['ec2', 'self-hosted']
        body = {
            'job_id': job_id,
            'job_labels': job_labels,
            'github_repo': github_repo,
            'runner_type': runner_type
        }
        if run_id is not None:
            body['run_id'] = run_id
        return {
            'path': '/v1/ec2-runner',
            'httpMethod': 'POST',
            'headers': {},
            'body': json.dumps(body)
        }
    return _create_event


@pytest.fixture
def ec2_runner_get_event():
    """Provide a GET event for EC2 runner endpoint."""
    return {
        'path': '/v1/ec2-runner',
        'httpMethod': 'GET',
        'headers': {}
    }


@pytest.fixture
def mock_boto_client():
    """Provide mocked boto3 clients for EC2, SSM, and DynamoDB."""
    mock_ec2 = MagicMock()
    mock_ssm = MagicMock()
    mock_dynamodb = MagicMock()

    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}

    mock_ec2.describe_images.return_value = {
        'Images': [
            {'ImageId': 'ami-test123', 'CreationDate': '2024-01-01T00:00:00Z'}
        ]
    }
    setup_mock_ec2_vpc_responses(mock_ec2)
    mock_ec2.describe_instances.return_value = {
        'Reservations': [{
            'Instances': [{
                'InstanceId': 'i-test123',
                'InstanceType': 't3.medium',
                'State': {'Name': 'running'},
                'Placement': {'AvailabilityZone': f'{TEST_AWS_REGION}a'}
            }]
        }]
    }
    mock_ec2.create_launch_template.return_value = {
        'LaunchTemplate': {'LaunchTemplateId': 'lt-test123'}
    }
    mock_ec2.create_fleet.return_value = {
        'Instances': [{'InstanceIds': ['i-test123']}]
    }

    with patch(
        'boto3.client',
        side_effect=create_multi_client_mock(mock_ec2, mock_ssm, dynamodb=mock_dynamodb)
    ):
        yield {'ec2': mock_ec2, 'ssm': mock_ssm, 'dynamodb': mock_dynamodb}


@pytest.fixture
def lambda_context():
    """Provide a mock Lambda context object."""
    return Mock()


def create_mock_ec2_with_ami():
    """Create a mock EC2 client with describe_images returning a valid AMI."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_images.return_value = {
        'Images': [{'ImageId': 'ami-test', 'CreationDate': '2024-01-01T00:00:00'}]
    }
    return mock_ec2


def get_minimal_env_vars():
    """Get minimal environment variables needed for launch tests."""
    return {
        'SUBNETS': 'subnet-1',
        'SECURITY_GROUPS': 'sg-1',
        'EC2_INSTANCE_TYPES': 't3.small',
        'EC2_IAM_INSTANCE_PROFILE': 'profile'
    }
