import importlib.util
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, Callable
from types import ModuleType
from unittest.mock import MagicMock, Mock, patch
from botocore.exceptions import ClientError
import pytest
import yaml


def parse_response_body(response: Dict[str, Any]) -> Any:
    return json.loads(response['body'])


def assert_response_status(response: Dict[str, Any], expected_code: int) -> None:
    assert response['statusCode'] == expected_code


def assert_json_content_type(response: Dict[str, Any]) -> None:
    assert response['headers']['Content-Type'] == 'application/json'


def assert_cors_headers(response: Dict[str, Any]) -> None:
    assert 'Access-Control-Allow-Origin' in response['headers']


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


def get_lambda_path(filename: str) -> Path:
    return Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambdas" / filename


def load_handler_module(relative_path: str, module_name: str) -> ModuleType:
    base_path = Path(__file__).parent.parent.parent.parent / "src" / "api"
    handler_path = base_path / relative_path
    spec = importlib.util.spec_from_file_location(module_name, handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_lambda_module(filename: str, module_name: str) -> ModuleType:
    handler_path = get_lambda_path(filename)
    spec = importlib.util.spec_from_file_location(module_name, handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_lambda_response_payload(response: Any) -> Any:
    return json.loads(response['Payload'].read())


@pytest.fixture
def openapi_spec() -> Dict[str, Any]:
    openapi_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "files" / "openapi.yml"
    with open(openapi_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture
def health_handler() -> ModuleType:
    return load_lambda_module("health.py", "health_handler")


@pytest.fixture
def v1_handler(config: Dict[str, str]) -> Any:
    env_vars = {
        'AWS_REGION': config['aws_region'],
        'ECR_REPOSITORY': config['ecr_repository_name'],
        'GITHUB_REPO': config['github_repo'],
        'GITHUB_TOKEN_SECRET_NAME': '/github/pat',
        'ECS_CLUSTER': config['cluster_name'],
        'CONTAINER_NAME': config['container_name'],
        'TASK_DEFINITION': config['task_family'],
        'EC2_INSTANCE_TYPES': ','.join(config['ec2_spot_instance_types']),
        'EC2_MAX_PRICE': config['ec2_max_spot_price'],
        'API_DOMAIN': config['domain_subdomain'],
        'IMAGE_API_ENDPOINT': f"https://{config['domain_subdomain']}/{config['api_version']}",
        'SUBNETS': 'subnet-test1,subnet-test2',
        'SECURITY_GROUPS': 'sg-test',
        'VPC_ID': 'vpc-test',
        'EC2_IAM_INSTANCE_PROFILE': 'test-profile'
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("v1.py", "v1_handler")
        if hasattr(module, '_clients'):
            setattr(module, '_clients', {})
        if hasattr(module, '_github_token_cache'):
            setattr(module, '_github_token_cache', {'value': None})
        yield module


@pytest.fixture
def catchall_handler():
    return load_lambda_module("catchall.py", "catchall_handler")


@pytest.fixture
def webhook_router(config):
    env_vars = {
        'API_KEY_PARAMETER_NAME': config['ssm_parameter_name_for_api_key'],
        'WEBHOOK_SECRET_NAME': config['ssm_parameter_name_for_webhook_secret'],
        'API_BASE_URL': f"https://{config['domain_subdomain']}/{config['api_version']}"
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("webhook_router.py", "webhook_router")
        if hasattr(module, '_clients'):
            setattr(module, '_clients', {'ssm': None, 'dynamodb': None, 'sqs': None, 'cloudwatch': None})
        if hasattr(module, '_webhook_secret_cache'):
            setattr(module, '_webhook_secret_cache', {'value': None})
        if hasattr(module, '_api_key_cache'):
            setattr(module, '_api_key_cache', {'value': None})
        if hasattr(module, '_circuit_breaker_state'):
            setattr(module, '_circuit_breaker_state', {'failures': 0, 'last_failure_time': 0.0, 'state': 'closed'})
        yield module


@pytest.fixture
def circuit_breaker_remediation(config):
    env_vars = {
        'AWS_REGION': config['aws_region']
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("circuit_breaker_remediation.py", "circuit_breaker_remediation")
        yield module


@pytest.fixture
def dlq_reprocessor(config):
    env_vars = {
        'AWS_REGION': config['aws_region']
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("dlq_reprocessor.py", "dlq_reprocessor")
        yield module


@pytest.fixture
def circuit_breaker_recovery(config):
    env_vars = {
        'AWS_REGION': config['aws_region']
    }
    with patch.dict('os.environ', env_vars):
        module = load_lambda_module("circuit_breaker_recovery.py", "circuit_breaker_recovery")
        yield module


@pytest.fixture
def mock_sqs():
    with patch('boto3.client') as mock_boto_client:
        mock_sqs_client = MagicMock()
        mock_boto_client.return_value = mock_sqs_client
        yield mock_sqs_client


@pytest.fixture
def mock_dynamodb():
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb_client = MagicMock()
        mock_boto_client.return_value = mock_dynamodb_client
        yield mock_dynamodb_client


@pytest.fixture
def mock_ssm():
    with patch('boto3.client') as mock_boto_client:
        mock_ssm_client = MagicMock()
        mock_ssm_client.get_parameter.return_value = {
            'Parameter': {'Value': 'test-token'}
        }
        mock_boto_client.return_value = mock_ssm_client
        yield mock_ssm_client


@pytest.fixture
def mock_cloudwatch():
    with patch('boto3.client') as mock_boto_client:
        mock_cw_client = MagicMock()
        mock_boto_client.return_value = mock_cw_client
        yield mock_cw_client


@pytest.fixture
def lambda_context():
    return Mock()


@pytest.fixture
def health_get_event():
    return {'path': '/health', 'httpMethod': 'GET'}


@pytest.fixture
def catchall_unknown_event():
    return {'path': '/unknown', 'httpMethod': 'GET'}


@pytest.fixture
def echo_post_event_factory():
    def _create_event(body_data=None, is_base64_encoded=False, content_type='application/json'):
        if body_data is None:
            body_data = {'test': 'data'}
        return {
            'path': '/v1/echo',
            'httpMethod': 'POST',
            'body': json.dumps(body_data) if not is_base64_encoded else body_data,
            'isBase64Encoded': is_base64_encoded,
            'headers': {'Content-Type': content_type},
            'requestContext': {'requestId': 'test-request-id'}
        }
    return _create_event


@pytest.fixture
def docker_runner_post_event_factory():
    def _create_event(job_id=123, job_labels=None, github_repo='test/repo'):
        if job_labels is None:
            job_labels = ['fargate', 'self-hosted']
        return {
            'path': '/v1/docker-runner',
            'httpMethod': 'POST',
            'body': json.dumps({
                'job_id': job_id,
                'job_labels': job_labels,
                'github_repo': github_repo
            })
        }
    return _create_event


@pytest.fixture
def ec2_runner_post_event_factory():
    def _create_event(job_id=456, job_labels=None, github_repo='test/repo'):
        if job_labels is None:
            job_labels = ['ec2', 'self-hosted']
        return {
            'path': '/v1/ec2-runner',
            'httpMethod': 'POST',
            'body': json.dumps({
                'job_id': job_id,
                'job_labels': job_labels,
                'github_repo': github_repo
            })
        }
    return _create_event


@pytest.fixture
def image_docker_event_factory():
    def _create_event(method='POST', path_suffix=''):
        return {
            'path': f'/v1/image-for-docker-runners{path_suffix}',
            'httpMethod': method,
            'body': json.dumps({}) if method == 'POST' else None,
            'pathParameters': {'digest': 'sha256:test'} if 'digest' in path_suffix else None
        }
    return _create_event


@pytest.fixture
def image_ec2_event_factory():
    def _create_event(method='POST', path_suffix='', ami_id='ami-test123'):
        return {
            'path': f'/v1/image-for-ec2-runners{path_suffix}',
            'httpMethod': method,
            'body': json.dumps({}) if method == 'POST' else None,
            'pathParameters': {'ami_id': ami_id} if ami_id and method == 'DELETE' else None
        }
    return _create_event


@pytest.fixture
def workflow_job_event_factory():
    def _create_event(action='queued', job_id=123, labels=None, repo='test/repo', run_id=456):
        if labels is None:
            labels = ['self-hosted', 'linux']
        return {
            'path': '/v1/runners',
            'httpMethod': 'POST',
            'headers': {
                'X-GitHub-Event': 'workflow_job',
                'X-Hub-Signature-256': 'sha256=test'
            },
            'body': json.dumps({
                'action': action,
                'workflow_job': {
                    'id': job_id,
                    'run_id': run_id,
                    'labels': labels,
                    'status': 'queued' if action == 'queued' else 'completed'
                },
                'repository': {
                    'full_name': repo
                }
            })
        }
    return _create_event


@pytest.fixture
def sqs_event_factory():
    def _create_event(records=None):
        if records is None:
            records = [{
                'messageId': 'test-message-id',
                'body': json.dumps({'job_id': 123, 'action': 'test'}),
                'attributes': {},
                'messageAttributes': {}
            }]
        return {
            'Records': records
        }
    return _create_event


@pytest.fixture
def dlq_message_factory():
    def _create_event(body=None, receipt_handle='test-receipt', attributes=None):
        if body is None:
            body = {'job_id': 123, 'action': 'test'}
        if attributes is None:
            attributes = {'ApproximateReceiveCount': '1'}
        return {
            'MessageId': 'test-message-id',
            'ReceiptHandle': receipt_handle,
            'Body': json.dumps(body),
            'Attributes': attributes,
            'MessageAttributes': {}
        }
    return _create_event


@pytest.fixture
def circuit_breaker_closed_state():
    return {
        'state': 'closed',
        'failure_count': 0,
        'last_failure_time': None
    }


@pytest.fixture
def circuit_breaker_open_state():
    return {
        'state': 'open',
        'failure_count': 5,
        'last_failure_time': time.time()
    }


@pytest.fixture
def mock_urllib_response_factory():
    def _create_response(read_value=b'', status=200, json_data=None):
        mock_response = Mock()
        if json_data is not None:
            mock_response.read.return_value = json.dumps(json_data).encode()
        else:
            mock_response.read.return_value = read_value
        mock_response.status = status
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        return mock_response
    return _create_response


def create_multi_client_mock(ec2_mock: Any, ssm_mock: Any) -> Callable:
    def mock_client(service_name: str) -> Any:
        if service_name == 'ec2':
            return ec2_mock
        if service_name == 'ssm':
            return ssm_mock
        return MagicMock()
    return mock_client


def assert_no_hardcoded_env_defaults(lambda_path: Path) -> None:
    with open(lambda_path, 'r', encoding='utf-8') as f:
        content = f.read()
    os_environ_get_pattern_with_default = r"os\.environ\.get\(['\"][^'\"]+['\"],\s*['\"]"
    matches = re.findall(os_environ_get_pattern_with_default, content)
    assert len(matches) == 0


TEST_CONSTANTS = {
    'queue_url': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue',
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
    'task_arn_full': 'arn:aws:ecs:us-east-1:123456789012:task/test',
    'test_timestamp': '2024-01-01T00:00:00',
    'aws_account_id': '123456789012',
    'aws_region': 'us-east-1',
}


ENV_VAR_PRESETS = {
    'base': {
        'AWS_REGION': 'us-east-1',
    },
    'v1_handler': {
        'AWS_REGION': 'us-east-1',
        'ECR_REPOSITORY': 'test-ecr-repo',
        'GITHUB_REPO': 'test/repo',
        'GITHUB_TOKEN_SECRET_NAME': 'test-github-token',
        'ECS_CLUSTER': 'test-cluster',
        'CONTAINER_NAME': 'test-container',
        'TASK_DEFINITION': 'test-task-family',
        'EC2_INSTANCE_TYPES': 't3.micro,t3.small',
        'EC2_MAX_PRICE': '0.05',
        'API_DOMAIN': 'api.test.com',
        'IMAGE_API_ENDPOINT': 'https://api.test.com/v1',
        'SUBNETS': 'subnet-test1,subnet-test2',
        'SECURITY_GROUPS': 'sg-test',
        'VPC_ID': 'vpc-test',
        'EC2_IAM_INSTANCE_PROFILE': 'test-profile',
    },
    'webhook_router': {
        'AWS_REGION': 'us-east-1',
        'API_KEY_PARAMETER_NAME': 'test-api-key-param',
        'WEBHOOK_SECRET_NAME': 'test-webhook-secret',
        'API_BASE_URL': 'https://api.test.com/v1',
        'IDEMPOTENCY_TABLE_NAME': 'test-table',
        'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue',
    },
}


def create_boto_client_mock(**service_mocks: Any) -> Callable:
    def mock_client(service_name: str) -> Any:
        return service_mocks.get(service_name, MagicMock())
    return mock_client


def reset_module_state(module: ModuleType, **state_vars: Any) -> None:
    for var_name, default_value in state_vars.items():
        if hasattr(module, var_name):
            setattr(module, var_name, default_value)


def create_mock_lambda_list_mappings_error():
    mock_lambda = MagicMock()
    mock_lambda.list_event_source_mappings.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable'}},
        'ListEventSourceMappings'
    )
    return mock_lambda


def create_mock_lambda_put_concurrency_error():
    mock_lambda = MagicMock()
    mock_lambda.put_function_concurrency.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable'}},
        'PutFunctionConcurrency'
    )
    return mock_lambda


def create_mock_sns_publish_error():
    mock_sns = MagicMock()
    mock_sns.publish.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable'}},
        'Publish'
    )
    return mock_sns


def create_mock_lambda_with_mappings():
    mock_lambda = MagicMock()
    mock_lambda.list_event_source_mappings.return_value = {
        'EventSourceMappings': [{'UUID': 'test-uuid', 'State': 'Enabled'}]
    }
    return mock_lambda
