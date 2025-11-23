import ast
import importlib.util
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
import boto3
from botocore.exceptions import ClientError
import pytest
import yaml


@pytest.fixture
def cfg():
    tfvars_path = Path(__file__).parent.parent.parent / "src" / "api" / "terraform.tfvars"
    tfvars = {}
    with open(tfvars_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                if value.startswith('['):
                    value = ast.literal_eval(value)
                elif value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                tfvars[key] = value

    return {
        "aws": {
            "account_id": tfvars.get("aws_account_id"),
            "region": tfvars.get("aws_region")
        },
        "naming": {
            "vpc_name": tfvars.get("vpc_name")
        },
        "github": {
            "runner_version": tfvars.get("github_runner_version")
        }
    }


@pytest.fixture
def openapi_spec():
    openapi_path = Path(__file__).parent.parent.parent / "src" / "api" / "files" / "openapi.yml"
    with open(openapi_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture
def health_handler():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "lambdas" / "health.py"
    spec = importlib.util.spec_from_file_location("health_handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def v1_handler():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "lambdas" / "v1.py"
    spec = importlib.util.spec_from_file_location("v1_handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def catchall_handler():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "lambdas" / "catchall.py"
    spec = importlib.util.spec_from_file_location("catchall_handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="apigw_client")
def apigw_client_fixture(cfg):
    return boto3.client('apigateway', region_name=cfg['aws']['region'])


@pytest.fixture(name="lambda_client")
def lambda_client_fixture(cfg):
    return boto3.client('lambda', region_name=cfg['aws']['region'])


@pytest.fixture(name="cloudformation_client")
def cloudformation_client_fixture(cfg):
    return boto3.client('cloudformation', region_name=cfg['aws']['region'])


@pytest.fixture(name="acm_client")
def acm_client_fixture(cfg):
    return boto3.client('acm', region_name=cfg['aws']['region'])


@pytest.fixture(name="s3_client")
def s3_client_fixture(cfg):
    return boto3.client('s3', region_name=cfg['aws']['region'])


@pytest.fixture(name="api_id")
def api_id_fixture(apigw_client):
    apis = apigw_client.get_rest_apis()
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            return api['id']
    return None


@pytest.fixture(name="health_function_name")
def health_function_name_fixture(lambda_client):
    return find_lambda_by_substring(lambda_client, 'HealthHandler')


@pytest.fixture(name="echo_function_name")
def echo_function_name_fixture(lambda_client):
    return find_lambda_by_substring(lambda_client, 'V1ApiHandler')


@pytest.fixture(name="stack_outputs")
def stack_outputs_fixture(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    return stacks['Stacks'][0].get('Outputs', [])


@pytest.fixture(name="certificate_arn")
def certificate_arn_fixture(acm_client):
    subdomain = "api.10ulabs.com"
    certificates = acm_client.list_certificates()
    for cert in certificates['CertificateSummaryList']:
        if cert['DomainName'] == subdomain:
            return cert['CertificateArn']
    return None


@pytest.fixture(name="bucket_name")
def bucket_name_fixture():
    return "api.10ulabs.com"


@pytest.fixture(name="api_endpoint")
def api_endpoint_fixture(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    outputs = stacks['Stacks'][0].get('Outputs', [])

    for output in outputs:
        if output['OutputKey'] == 'ApiEndpoint':
            return output['OutputValue']

    return "https://api.10ulabs.com"


@pytest.fixture
def webhook_router():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "lambdas" / "webhook_router.py"
    spec = importlib.util.spec_from_file_location("webhook_router", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, '_clients'):
        setattr(module, '_clients', {'ssm': None, 'dynamodb': None, 'sqs': None, 'cloudwatch': None})
    if hasattr(module, '_webhook_secret_cache'):
        setattr(module, '_webhook_secret_cache', {'value': None})
    if hasattr(module, '_circuit_breaker_state'):
        setattr(module, '_circuit_breaker_state', {'failures': 0, 'last_failure_time': 0.0, 'state': 'closed'})
    return module


@pytest.fixture
def circuit_breaker_remediation():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "lambdas" / "circuit_breaker_remediation.py"
    spec = importlib.util.spec_from_file_location("circuit_breaker_remediation", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def dlq_reprocessor():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "lambdas" / "dlq_reprocessor.py"
    spec = importlib.util.spec_from_file_location("dlq_reprocessor", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
def cfn_event_factory():
    def _create_event(request_type='Create', properties=None, physical_resource_id=None):
        if properties is None:
            properties = {'GitHubRepo': 'test/repo', 'WebhookUrl': 'https://test.com'}
        event = {
            'RequestType': request_type,
            'ServiceToken': 'arn:aws:lambda:us-east-1:123456789:function:test',
            'ResponseURL': 'https://cloudformation-response.test.com',
            'StackId': 'arn:aws:cloudformation:us-east-1:123456789:stack/test/guid',
            'RequestId': 'test-request-id',
            'LogicalResourceId': 'TestResource',
            'ResourceType': 'Custom::GitHubWebhook',
            'ResourceProperties': properties
        }
        if physical_resource_id and request_type in ['Update', 'Delete']:
            event['PhysicalResourceId'] = physical_resource_id
        return event
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
def mock_github_api_success():
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.read.return_value = json.dumps({'token': 'test-token'}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        yield mock_urlopen


@pytest.fixture
def env_with_queue_urls():
    env_vars = {
        'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-queue',
        'WEBHOOK_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/webhook-dlq',
        'JOB_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-dlq'
    }
    with patch.dict('os.environ', env_vars):
        yield env_vars


@pytest.fixture
def env_with_function_name():
    with patch.dict('os.environ', {'FUNCTION_NAME': 'test-function'}):
        yield


@pytest.fixture
def env_with_webhook_function_name():
    with patch.dict('os.environ', {'WEBHOOK_FUNCTION_NAME': 'test-function'}):
        yield


@pytest.fixture
def mock_lambda_invoke_factory():
    def _create_response(status_code=200, payload=None):
        if payload is None:
            payload = {'statusCode': status_code, 'body': json.dumps({'status': 'healthy'})}
        response = MagicMock()
        response['StatusCode'] = status_code
        response['Payload'] = MagicMock()
        response['Payload'].read.return_value = json.dumps(payload).encode()
        return response
    return _create_response


@pytest.fixture
def api_src_path():
    return Path(__file__).parent.parent.parent / "src" / "api"


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


@pytest.fixture
def mock_boto3_client_factory():
    def _create_mock_client(method_returns=None):
        mock_client = MagicMock()
        if method_returns:
            for method_name, return_value in method_returns.items():
                getattr(mock_client, method_name).return_value = return_value
        return mock_client
    return _create_mock_client


@pytest.fixture
def mock_multi_boto3_clients():
    def _create_clients(*service_names):
        clients = {}
        for service in service_names:
            clients[service] = MagicMock()

        def client_side_effect(service_name):
            return clients.get(service_name, MagicMock())

        return clients, client_side_effect
    return _create_clients


@pytest.fixture
def env_with_ec2_config():
    env_vars = {
        'AWS_REGION': 'us-east-1',
        'SUBNETS': 'subnet-123,subnet-456,subnet-789',
        'SECURITY_GROUPS': 'sg-12345',
        'VPC_ID': 'vpc-test123',
        'EC2_INSTANCE_TYPES': 't4g.large,t4g.medium',
        'EC2_IAM_INSTANCE_PROFILE': 'TestInstanceProfile',
        'EC2_MAX_PRICE': '0.10',
        'GITHUB_TOKEN': 'ghp_test_token',
        'API_DOMAIN': 'api.test.com'
    }
    with patch.dict('os.environ', env_vars, clear=False):
        yield env_vars


def load_handler_module(relative_path, module_name):
    base_path = Path(__file__).parent.parent.parent / "src" / "api"
    handler_path = base_path / relative_path
    spec = importlib.util.spec_from_file_location(module_name, handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_lambda_response_payload(response):
    return json.loads(response['Payload'].read())


@pytest.fixture
def sqs_receive_message_factory():
    def _create_response(messages=None):
        if messages is None:
            messages = [{
                'Body': json.dumps({'test': 'data'}),
                'ReceiptHandle': 'receipt-1',
                'MessageAttributes': {},
                'Attributes': {}
            }]
        return {'Messages': messages}
    return _create_response


def find_lambda_by_substring(lambda_client, substring):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    matches = [name for name in function_names if substring in name]
    return matches[0] if matches else None


@pytest.fixture(name="ssm_client")
def ssm_client_fixture(cfg):
    return boto3.client('ssm', region_name=cfg['aws']['region'])


@pytest.fixture(name="api_key")
def api_key_fixture(ssm_client):
    try:
        response = ssm_client.get_parameter(Name='/api/key', WithDecryption=True)
        return response['Parameter']['Value']
    except ClientError:
        return None


@pytest.fixture(name="ecr_client")
def ecr_client_fixture(cfg):
    return boto3.client('ecr', region_name=cfg['aws']['region'])


@pytest.fixture(name="ecr_image_count")
def ecr_image_count_fixture(ecr_client):
    try:
        response = ecr_client.describe_images(
            repositoryName='github-runner',
            filter={'tagStatus': 'TAGGED'}
        )
        stable_images = [
            img for img in response.get('imageDetails', [])
            if 'stable' in img.get('imageTags', [])
        ]
        return len(stable_images)
    except ClientError:
        return 0
