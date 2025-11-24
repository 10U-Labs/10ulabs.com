import importlib.util
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from botocore.exceptions import ClientError
import pytest
import yaml


def parse_response_body(response):
    return json.loads(response['body'])


def assert_response_status(response, expected_code):
    assert response['statusCode'] == expected_code


def assert_json_content_type(response):
    assert response['headers']['Content-Type'] == 'application/json'


def assert_cors_headers(response):
    assert 'Access-Control-Allow-Origin' in response['headers']


def create_client_error(error_code, operation_name='TestOperation'):
    return ClientError(
        {
            'Error': {
                'Code': error_code,
                'Message': f'Test error: {error_code}'
            },
            'ResponseMetadata': {
                'RequestId': 'test-request-id',
                'HTTPStatusCode': 400
            }
        },
        operation_name
    )


def load_handler_module(relative_path, module_name):
    base_path = Path(__file__).parent.parent.parent.parent / "src" / "api"
    handler_path = base_path / relative_path
    spec = importlib.util.spec_from_file_location(module_name, handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_lambda_response_payload(response):
    return json.loads(response['Payload'].read())


@pytest.fixture
def openapi_spec():
    openapi_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "files" / "openapi.yml"
    with open(openapi_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture
def health_handler():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambdas" / "health.py"
    spec = importlib.util.spec_from_file_location("health_handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def v1_handler(tfvars):
    env_vars = {
        'AWS_REGION': tfvars['aws_region'],
        'ECR_REPOSITORY': tfvars['ecr_repository_name'],
        'GITHUB_REPO': tfvars['github_repo'],
        'GITHUB_TOKEN_SECRET_NAME': tfvars['github_token_secret_name'],
        'ECS_CLUSTER': tfvars['cluster_name'],
        'CONTAINER_NAME': tfvars['container_name'],
        'TASK_DEFINITION': tfvars['task_family'],
        'EC2_INSTANCE_TYPES': ','.join(tfvars['ec2_spot_instance_types']),
        'EC2_MAX_PRICE': tfvars['ec2_max_spot_price'],
        'API_DOMAIN': tfvars['domain_subdomain'],
        'IMAGE_API_ENDPOINT': f"https://{tfvars['domain_subdomain']}/{tfvars['api_version']}",
        'SUBNETS': 'subnet-test1,subnet-test2',
        'SECURITY_GROUPS': 'sg-test',
        'VPC_ID': 'vpc-test',
        'EC2_IAM_INSTANCE_PROFILE': 'test-profile'
    }
    with patch.dict('os.environ', env_vars):
        handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambdas" / "v1.py"
        spec = importlib.util.spec_from_file_location("v1_handler", handler_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, '_clients'):
            setattr(module, '_clients', {})
        if hasattr(module, '_github_token_cache'):
            setattr(module, '_github_token_cache', {'value': None})
        yield module


@pytest.fixture
def catchall_handler():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambdas" / "catchall.py"
    spec = importlib.util.spec_from_file_location("catchall_handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def webhook_router(tfvars):
    env_vars = {
        'API_KEY_PARAMETER_NAME': tfvars['api_key_parameter_name'],
        'WEBHOOK_SECRET_NAME': tfvars['webhook_secret_name'],
        'API_BASE_URL': f"https://{tfvars['domain_subdomain']}/{tfvars['api_version']}"
    }
    with patch.dict('os.environ', env_vars):
        handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambdas" / "webhook_router.py"
        spec = importlib.util.spec_from_file_location("webhook_router", handler_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
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
def circuit_breaker_remediation(tfvars):
    env_vars = {
        'AWS_REGION': tfvars['aws_region']
    }
    with patch.dict('os.environ', env_vars):
        handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambdas" / "circuit_breaker_remediation.py"
        spec = importlib.util.spec_from_file_location("circuit_breaker_remediation", handler_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module


@pytest.fixture
def dlq_reprocessor(tfvars):
    env_vars = {
        'AWS_REGION': tfvars['aws_region']
    }
    with patch.dict('os.environ', env_vars):
        handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambdas" / "dlq_reprocessor.py"
        spec = importlib.util.spec_from_file_location("dlq_reprocessor", handler_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
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
