import importlib.util
import json
from pathlib import Path
from typing import Any, Callable, Dict
from types import ModuleType
from unittest.mock import MagicMock, Mock, patch

import pytest
from botocore.exceptions import ClientError

from test.api.endpoints.ec2_runner.conftest import EC2_RUNNER_SRC


def load_handler_module() -> ModuleType:
    handler_path = EC2_RUNNER_SRC / "lambda" / "handler.py"
    spec = importlib.util.spec_from_file_location("ec2_runner_handler", handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def ec2_runner_handler(config: Dict[str, str]) -> Any:
    env_vars = {
        'AWS_REGION': config['aws_region'],
        'EC2_AMI_PURPOSE_TAG': 'Purpose',
        'EC2_AMI_PURPOSE_VALUE': 'GitHub self-hosted EC2 runner',
        'EC2_AMI_STABLE_TAG': 'Stable',
        'EC2_MANAGED_BY_TAG': 'api-ec2-spot-runner',
        'GITHUB_REPO': config['github_repo'],
        'GITHUB_TOKEN_SECRET_NAME': config['ssm_parameter_name_for_github_pat'],
        'EC2_INSTANCE_TYPES': ','.join(config['ec2_spot_instance_types']),
        'EC2_MAX_PRICE': config['ec2_max_spot_price'],
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
        if hasattr(module, '_clients'):
            setattr(module, '_clients', {})
        if hasattr(module, '_github_token_cache'):
            setattr(module, '_github_token_cache', {'value': None})
        if hasattr(module, '_api_key_cache'):
            setattr(module, '_api_key_cache', {'value': None})
        if hasattr(module, '_dependencies_validated'):
            setattr(module, '_dependencies_validated', {'checked': True, 'valid': True, 'errors': []})
        yield module


@pytest.fixture
def lambda_context():
    return Mock()


@pytest.fixture
def ec2_runner_post_event_factory():
    def _create_event(job_id=456, job_labels=None, github_repo='test/repo', run_id=None, runner_type='ec2'):
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
    return {
        'path': '/v1/ec2-runner',
        'httpMethod': 'GET',
        'headers': {}
    }


def create_client_error(error_code: str, operation_name: str = 'TestOperation') -> ClientError:
    return ClientError(
        {
            'Error': {
                'Code': error_code,
                'Message': f'Test error: {error_code}'
            },
            'ResponseMetadata': {
                'RequestId': 'test-request-id',
                'HTTPStatusCode': 400,
                'HTTPHeaders': {},
                'RetryAttempts': 0,
                'HostId': ''
            }
        },
        operation_name
    )


def parse_response_body(response: Dict[str, Any]) -> Any:
    return json.loads(response['body'])


def assert_response_status(response: Dict[str, Any], expected_code: int) -> None:
    assert response['statusCode'] == expected_code


def assert_json_content_type(response: Dict[str, Any]) -> None:
    assert response['headers']['Content-Type'].startswith('application/json')


def create_multi_client_mock(ec2_mock: Any, ssm_mock: Any, dynamodb_mock: Any = None) -> Callable:
    def mock_client(service_name: str) -> Any:
        if service_name == 'ec2':
            return ec2_mock
        if service_name == 'ssm':
            return ssm_mock
        if service_name == 'dynamodb':
            return dynamodb_mock if dynamodb_mock else MagicMock()
        return MagicMock()
    return mock_client


@pytest.fixture
def mock_boto_client():
    mock_ec2 = MagicMock()
    mock_ssm = MagicMock()
    mock_dynamodb = MagicMock()

    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}

    mock_ec2.describe_images.return_value = {
        'Images': [
            {'ImageId': 'ami-test123', 'CreationDate': '2024-01-01T00:00:00Z'}
        ]
    }
    mock_ec2.describe_security_groups.return_value = {
        'SecurityGroups': [{'GroupId': 'sg-test'}]
    }
    mock_ec2.describe_subnets.return_value = {
        'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]
    }
    mock_ec2.describe_vpcs.return_value = {
        'Vpcs': [{'VpcId': 'vpc-test'}]
    }
    mock_ec2.describe_instances.return_value = {
        'Reservations': [{
            'Instances': [{
                'InstanceId': 'i-test123',
                'InstanceType': 't3.medium',
                'State': {'Name': 'running'},
                'Placement': {'AvailabilityZone': 'us-east-1a'}
            }]
        }]
    }
    mock_ec2.create_launch_template.return_value = {
        'LaunchTemplate': {'LaunchTemplateId': 'lt-test123'}
    }
    mock_ec2.create_fleet.return_value = {
        'Instances': [{'InstanceIds': ['i-test123']}]
    }

    with patch('boto3.client', side_effect=create_multi_client_mock(mock_ec2, mock_ssm, mock_dynamodb)):
        yield {'ec2': mock_ec2, 'ssm': mock_ssm, 'dynamodb': mock_dynamodb}
