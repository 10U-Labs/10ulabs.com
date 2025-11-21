import json
from pathlib import Path
import importlib.util
import boto3
import pytest
import yaml
import aws_cdk as cdk
from aws_cdk.assertions import Template


@pytest.fixture
def config():
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def openapi_spec():
    openapi_path = Path(__file__).parent.parent.parent / "src" / "api" / "openapi.yml"
    with open(openapi_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture
def api_stack_class():
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    return api_module.ApiStack


@pytest.fixture
def cdk_app():
    return cdk.App()


@pytest.fixture
def api_stack(cdk_app, api_stack_class, config):
    return api_stack_class(
        cdk_app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )


@pytest.fixture
def cdk_template(api_stack):
    return Template.from_stack(api_stack)


@pytest.fixture
def health_handler():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "endpoints" / "health" / "handler.py"
    spec = importlib.util.spec_from_file_location("health_handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def v1_handler():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "handler.py"
    spec = importlib.util.spec_from_file_location("v1_handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def catchall_handler():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "endpoints" / "catchall" / "handler.py"
    spec = importlib.util.spec_from_file_location("catchall_handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def apigw_client(config):
    return boto3.client('apigateway', region_name=config['aws']['region'])


@pytest.fixture
def lambda_client(config):
    return boto3.client('lambda', region_name=config['aws']['region'])


@pytest.fixture
def cloudformation_client(config):
    return boto3.client('cloudformation', region_name=config['aws']['region'])


@pytest.fixture
def acm_client(config):
    return boto3.client('acm', region_name=config['aws']['region'])


@pytest.fixture
def s3_client(config):
    return boto3.client('s3', region_name=config['aws']['region'])


@pytest.fixture
def api_id(apigw_client):
    apis = apigw_client.get_rest_apis()
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            return api['id']
    return None


@pytest.fixture
def health_function_name(lambda_client):
    return find_lambda_by_substring(lambda_client, 'HealthHandler')


@pytest.fixture
def echo_function_name(lambda_client):
    return find_lambda_by_substring(lambda_client, 'V1ApiHandler')


@pytest.fixture
def stack_outputs(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    return stacks['Stacks'][0].get('Outputs', [])


@pytest.fixture
def certificate_arn(acm_client, config):
    subdomain = config['domain_names']['subdomain']
    certificates = acm_client.list_certificates()
    for cert in certificates['CertificateSummaryList']:
        if cert['DomainName'] == subdomain:
            return cert['CertificateArn']
    return None


@pytest.fixture
def bucket_name(config):
    return config['domain_names']['subdomain']


@pytest.fixture
def api_endpoint(cloudformation_client, config):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    outputs = stacks['Stacks'][0].get('Outputs', [])

    for output in outputs:
        if output['OutputKey'] == 'ApiEndpoint':
            return output['OutputValue']

    subdomain = config['domain_names']['subdomain']
    return f"https://{subdomain}"


@pytest.fixture
def webhook_router():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "webhook_router.py"
    spec = importlib.util.spec_from_file_location("webhook_router", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def configure_webhook():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "configure_webhook_handler.py"
    spec = importlib.util.spec_from_file_location("configure_webhook", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def circuit_breaker_remediation():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "circuit_breaker_remediation.py"
    spec = importlib.util.spec_from_file_location("circuit_breaker_remediation", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def dlq_reprocessor():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "dlq_reprocessor.py"
    spec = importlib.util.spec_from_file_location("dlq_reprocessor", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def mock_sqs():
    from unittest.mock import MagicMock, patch
    with patch('boto3.client') as mock_boto_client:
        mock_sqs_client = MagicMock()
        mock_boto_client.return_value = mock_sqs_client
        yield mock_sqs_client


@pytest.fixture
def mock_dynamodb():
    from unittest.mock import MagicMock, patch
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb_client = MagicMock()
        mock_boto_client.return_value = mock_dynamodb_client
        yield mock_dynamodb_client


@pytest.fixture
def mock_ssm():
    from unittest.mock import MagicMock, patch
    with patch('boto3.client') as mock_boto_client:
        mock_ssm_client = MagicMock()
        mock_ssm_client.get_parameter.return_value = {
            'Parameter': {'Value': 'test-token'}
        }
        mock_boto_client.return_value = mock_ssm_client
        yield mock_ssm_client


@pytest.fixture
def mock_cloudwatch():
    from unittest.mock import MagicMock, patch
    with patch('boto3.client') as mock_boto_client:
        mock_cw_client = MagicMock()
        mock_boto_client.return_value = mock_cw_client
        yield mock_cw_client


@pytest.fixture
def lambda_context():
    from unittest.mock import Mock
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
    from botocore.exceptions import ClientError
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
    import time
    return {
        'state': 'open',
        'failure_count': 5,
        'last_failure_time': time.time()
    }


@pytest.fixture
def mock_github_api_success():
    from unittest.mock import MagicMock, patch
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.read.return_value = json.dumps({'token': 'test-token'}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        yield mock_urlopen


@pytest.fixture
def env_with_queue_urls():
    from unittest.mock import patch
    env_vars = {
        'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-queue',
        'WEBHOOK_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/webhook-dlq',
        'JOB_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-dlq'
    }
    with patch.dict('os.environ', env_vars):
        yield env_vars


@pytest.fixture
def env_with_function_name():
    from unittest.mock import patch
    with patch.dict('os.environ', {'FUNCTION_NAME': 'test-function'}):
        yield


@pytest.fixture
def env_with_webhook_function_name():
    from unittest.mock import patch
    with patch.dict('os.environ', {'WEBHOOK_FUNCTION_NAME': 'test-function'}):
        yield


@pytest.fixture
def mock_lambda_invoke_factory():
    def _create_response(status_code=200, payload=None):
        from unittest.mock import MagicMock
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


def find_lambda_by_substring(lambda_client, substring):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    matches = [name for name in function_names if substring in name]
    return matches[0] if matches else None
