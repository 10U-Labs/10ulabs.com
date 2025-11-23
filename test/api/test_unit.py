import base64
import json
import os
import time
import urllib.error
import urllib.parse
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from botocore.exceptions import ClientError
import pytest

from conftest import parse_response_body, assert_response_status, assert_json_content_type, assert_cors_headers


def test_config_file_exists_in_correct_location():
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "terraform.tfvars"
    assert config_path.exists()


def test_config_has_aws_account_id(cfg):
    assert "account_id" in cfg["aws"]


def test_config_has_aws_region(cfg):
    assert "region" in cfg["aws"]


def test_config_has_vpc_name(cfg):
    assert "vpc_name" in cfg["naming"]


def test_config_has_github_runner_version(cfg):
    assert "runner_version" in cfg["github"]


def test_terraform_tfvars_has_github_repo():
    tfvars_path = Path(__file__).parent.parent.parent / "src" / "api" / "terraform.tfvars"
    with open(tfvars_path, encoding="utf-8") as f:
        content = f.read()
    assert 'github_repo' in content


def test_terraform_tfvars_github_repo_format():
    tfvars_path = Path(__file__).parent.parent.parent / "src" / "api" / "terraform.tfvars"
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith('github_repo'):
                value = line.split('=')[1].strip().strip('"')
                assert '/' in value


def test_terraform_tfvars_has_domain_subdomain():
    tfvars_path = Path(__file__).parent.parent.parent / "src" / "api" / "terraform.tfvars"
    with open(tfvars_path, encoding="utf-8") as f:
        content = f.read()
    assert 'domain_subdomain' in content


def test_github_webhook_resource_exists():
    webhook_file = Path(__file__).parent.parent.parent / "src" / "api" / "github_webhook.tf"
    assert webhook_file.exists()


def test_github_webhook_resource_has_workflow_job_event():
    webhook_file = Path(__file__).parent.parent.parent / "src" / "api" / "github_webhook.tf"
    with open(webhook_file, encoding="utf-8") as f:
        content = f.read()
    assert 'workflow_job' in content


def test_github_webhook_resource_uses_runners_endpoint():
    webhook_file = Path(__file__).parent.parent.parent / "src" / "api" / "github_webhook.tf"
    with open(webhook_file, encoding="utf-8") as f:
        content = f.read()
    assert '/v1/runners' in content


def test_webhook_secret_uses_random_password():
    webhook_file = Path(__file__).parent.parent.parent / "src" / "api" / "github_webhook.tf"
    with open(webhook_file, encoding="utf-8") as f:
        content = f.read()
    assert 'random_password.webhook_secret' in content


def test_ssm_parameter_webhook_secret_uses_random_password():
    ssm_file = Path(__file__).parent.parent.parent / "src" / "api" / "ssm.tf"
    with open(ssm_file, encoding="utf-8") as f:
        content = f.read()
    assert 'random_password.webhook_secret.result' in content


def test_lambda_handler_health_endpoint_returns_200_status_code(health_handler, health_get_event, lambda_context):
    response = health_handler.handler(health_get_event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_health_endpoint_returns_json_content_type(health_handler, health_get_event, lambda_context):
    response = health_handler.handler(health_get_event, lambda_context)
    assert_json_content_type(response)


def test_lambda_handler_health_endpoint_returns_cors_header(health_handler, health_get_event, lambda_context):
    response = health_handler.handler(health_get_event, lambda_context)
    assert_cors_headers(response)


def test_lambda_handler_health_endpoint_body_contains_status(health_handler, health_get_event, lambda_context):
    response = health_handler.handler(health_get_event, lambda_context)
    body = parse_response_body(response)
    assert 'status' in body


def test_lambda_handler_health_endpoint_status_is_healthy(health_handler, health_get_event, lambda_context):
    response = health_handler.handler(health_get_event, lambda_context)
    body = parse_response_body(response)
    assert body['status'] == 'healthy'


def test_lambda_handler_echo_endpoint_returns_200_status_code(v1_handler, echo_post_event_factory, lambda_context):
    event = echo_post_event_factory()
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_echo_endpoint_returns_json_content_type(v1_handler, echo_post_event_factory, lambda_context):
    event = echo_post_event_factory()
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


def test_lambda_handler_echo_endpoint_echoes_input_data(v1_handler, echo_post_event_factory, lambda_context):
    payload = {'message': 'hello', 'number': 42}
    event = echo_post_event_factory(body_data=payload)
    response = v1_handler.lambda_handler(event, lambda_context)
    body = parse_response_body(response)
    assert body['echo'] == payload


def test_lambda_handler_echo_endpoint_includes_received_at(v1_handler, echo_post_event_factory, lambda_context):
    event = echo_post_event_factory()
    response = v1_handler.lambda_handler(event, lambda_context)
    body = parse_response_body(response)
    assert 'received_at' in body


def test_lambda_handler_echo_endpoint_with_invalid_json_returns_400(v1_handler, echo_post_event_factory, lambda_context):
    event = echo_post_event_factory()
    event['body'] = 'not valid json'
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_lambda_handler_catchall_returns_404_for_unknown_path(catchall_handler, catchall_unknown_event, lambda_context):
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    assert_response_status(response, 404)


def test_lambda_handler_catchall_returns_json_content_type(catchall_handler, catchall_unknown_event, lambda_context):
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    assert_json_content_type(response)


def test_lambda_handler_catchall_returns_cors_header(catchall_handler, catchall_unknown_event, lambda_context):
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    assert_cors_headers(response)


def test_lambda_handler_catchall_body_contains_error_message(catchall_handler, catchall_unknown_event, lambda_context):
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    body = parse_response_body(response)
    assert 'error' in body


def test_openapi_spec_file_exists():
    openapi_path = Path(__file__).parent.parent.parent / "src" / "api" / "files" / "openapi.yml"
    assert openapi_path.exists()


def test_openapi_spec_is_valid_yaml(openapi_spec):
    assert openapi_spec is not None


def test_openapi_spec_has_openapi_field(openapi_spec):
    assert 'openapi' in openapi_spec


def test_openapi_spec_version_starts_with_3_0(openapi_spec):
    assert openapi_spec['openapi'].startswith('3.0')


def test_openapi_spec_has_info_section(openapi_spec):
    assert 'info' in openapi_spec


def test_openapi_spec_info_has_title(openapi_spec):
    assert 'title' in openapi_spec['info']


def test_openapi_spec_info_has_version(openapi_spec):
    assert 'version' in openapi_spec['info']


def test_openapi_spec_has_paths_section(openapi_spec):
    assert 'paths' in openapi_spec


def test_openapi_spec_paths_not_empty(openapi_spec):
    assert len(openapi_spec['paths']) > 0


def test_openapi_spec_has_health_endpoint(openapi_spec):
    assert '/health' in openapi_spec['paths']


def test_openapi_spec_health_has_get_method(openapi_spec):
    assert 'get' in openapi_spec['paths']['/health']


def test_openapi_spec_has_echo_endpoint(openapi_spec):
    assert '/v1/echo' in openapi_spec['paths']


def test_openapi_spec_echo_has_post_method(openapi_spec):
    assert 'post' in openapi_spec['paths']['/v1/echo']


def test_openapi_spec_has_runners_post_endpoint(openapi_spec):
    assert '/v1/runners' in openapi_spec['paths']


def test_openapi_spec_runners_has_post_method(openapi_spec):
    assert 'post' in openapi_spec['paths']['/v1/runners']


def test_openapi_spec_has_runners_health_endpoint(openapi_spec):
    assert '/v1/runners/health' in openapi_spec['paths']


def test_openapi_spec_runners_health_has_get_method(openapi_spec):
    assert 'get' in openapi_spec['paths']['/v1/runners/health']


def test_openapi_spec_has_ec2_ami_base_endpoint(openapi_spec):
    assert '/v1/image-for-ec2-runners' in openapi_spec['paths']


def test_openapi_spec_has_ec2_ami_latest_endpoint(openapi_spec):
    assert '/v1/image-for-ec2-runners/latest' in openapi_spec['paths']


def test_openapi_spec_has_ec2_ami_delete_endpoint(openapi_spec):
    assert '/v1/image-for-ec2-runners/{ami_id}' in openapi_spec['paths']


def test_openapi_spec_has_docker_image_base_endpoint(openapi_spec):
    assert '/v1/image-for-docker-runners' in openapi_spec['paths']


def test_openapi_spec_has_docker_image_latest_endpoint(openapi_spec):
    assert '/v1/image-for-docker-runners/latest' in openapi_spec['paths']


def test_openapi_spec_has_docker_image_delete_endpoint(openapi_spec):
    assert '/v1/image-for-docker-runners/{digest}' in openapi_spec['paths']


def test_openapi_spec_has_docker_runner_endpoint(openapi_spec):
    assert '/v1/docker-runner' in openapi_spec['paths']


def test_openapi_spec_docker_runner_has_post_method(openapi_spec):
    assert 'post' in openapi_spec['paths']['/v1/docker-runner']


def test_openapi_spec_docker_runner_has_get_method(openapi_spec):
    assert 'get' in openapi_spec['paths']['/v1/docker-runner']


def test_openapi_spec_does_not_have_docker_runner_latest(openapi_spec):
    assert '/v1/docker-runner/latest' not in openapi_spec['paths']


def test_openapi_spec_has_ec2_runner_endpoint(openapi_spec):
    assert '/v1/ec2-runner' in openapi_spec['paths']


def test_openapi_spec_ec2_runner_has_post_method(openapi_spec):
    assert 'post' in openapi_spec['paths']['/v1/ec2-runner']


def test_openapi_spec_has_catchall_endpoint(openapi_spec):
    assert '/{proxy+}' in openapi_spec['paths']


def test_lambda_handler_docker_runner_post_with_missing_job_id_returns_400(v1_handler, docker_runner_post_event_factory, lambda_context):
    event = docker_runner_post_event_factory()
    body = parse_response_body({'body': event['body']})
    del body['job_id']
    event['body'] = json.dumps(body)
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_lambda_handler_docker_runner_post_with_missing_repo_returns_400(v1_handler, docker_runner_post_event_factory, lambda_context):
    event = docker_runner_post_event_factory()
    body = parse_response_body({'body': event['body']})
    del body['github_repo']
    event['body'] = json.dumps(body)
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


@patch('boto3.client')
def test_lambda_handler_docker_runner_post_returns_json_content_type(mock_boto_client, v1_handler, docker_runner_post_event_factory, lambda_context):
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [{'imageTags': ['stable'], 'imagePushedAt': '2024-01-01'}]
    }
    mock_ecs = MagicMock()
    mock_ecs.run_task.return_value = {'tasks': [{'taskArn': 'test-task'}]}
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}

    def mock_client(service_name):
        if service_name == 'ecr':
            return mock_ecr
        if service_name == 'ecs':
            return mock_ecs
        if service_name == 'ssm':
            return mock_ssm
        return MagicMock()

    mock_boto_client.side_effect = mock_client
    event = docker_runner_post_event_factory(job_id=12345, github_repo='10U-Labs-LLC/10ulabs.com')
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


@patch('boto3.client')
def test_lambda_handler_docker_runner_get_returns_json_content_type(mock_boto_client, v1_handler, lambda_context):
    mock_ecs = MagicMock()
    mock_ecs.list_tasks.return_value = {'taskArns': []}

    def mock_client(service_name):
        if service_name == 'ecs':
            return mock_ecs
        return MagicMock()

    mock_boto_client.side_effect = mock_client
    event = {'path': '/v1/docker-runner', 'httpMethod': 'GET'}
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


def test_lambda_handler_docker_runner_unsupported_method_returns_404(v1_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'DELETE'}
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 404)


def test_lambda_handler_ec2_runner_post_with_missing_job_id_returns_400(v1_handler, ec2_runner_post_event_factory, lambda_context):
    event = ec2_runner_post_event_factory()
    body = parse_response_body({'body': event['body']})
    del body['job_id']
    event['body'] = json.dumps(body)
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_lambda_handler_ec2_runner_post_with_missing_repo_returns_400(v1_handler, ec2_runner_post_event_factory, lambda_context):
    event = ec2_runner_post_event_factory()
    body = parse_response_body({'body': event['body']})
    del body['github_repo']
    event['body'] = json.dumps(body)
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


@patch.dict(os.environ, {'SUBNETS': 'subnet-123', 'SECURITY_GROUPS': 'sg-123', 'GITHUB_TOKEN_PARAM': '/github/token'})
@patch('boto3.client')
def test_lambda_handler_ec2_runner_post_returns_json_content_type(mock_boto_client, v1_handler, ec2_runner_post_event_factory, lambda_context):
    mock_ec2 = MagicMock()
    mock_ec2.describe_images.return_value = {
        'Images': [{'ImageId': 'ami-test123', 'CreationDate': '2024-01-01'}]
    }
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}

    def mock_client(service_name):
        if service_name == 'ec2':
            return mock_ec2
        if service_name == 'ssm':
            return mock_ssm
        return MagicMock()

    mock_boto_client.side_effect = mock_client
    event = ec2_runner_post_event_factory(job_id=12345, github_repo='10U-Labs-LLC/10ulabs.com')
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


def test_lambda_handler_image_for_docker_runners_post_returns_json_content_type(v1_handler, image_docker_event_factory, lambda_context):
    event = image_docker_event_factory(method='POST')
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


@patch('boto3.client')
def test_lambda_handler_image_for_docker_runners_get_returns_json_content_type(mock_boto_client, v1_handler, image_docker_event_factory, lambda_context):
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [{
            'imageTags': ['stable'],
            'imagePushedAt': datetime(2024, 1, 1),
            'imageDigest': 'sha256:abc123',
            'imageSizeInBytes': 1024000
        }]
    }

    def mock_client(service_name):
        if service_name == 'ecr':
            return mock_ecr
        return MagicMock()

    mock_boto_client.side_effect = mock_client
    event = image_docker_event_factory(method='GET')
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


def test_lambda_handler_image_for_docker_runners_delete_without_digest_returns_400(v1_handler, lambda_context):
    event = {
        'path': '/v1/image-for-docker-runners/sha256:abc123',
        'httpMethod': 'DELETE',
        'pathParameters': {}
    }
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


@patch('boto3.client')
def test_lambda_handler_image_for_docker_runners_delete_returns_json_content_type(mock_boto_client, v1_handler, lambda_context):
    mock_ecr = MagicMock()
    mock_ecr.batch_delete_image.return_value = {'imageIds': [{'imageDigest': 'sha256:abc123'}]}

    def mock_client(service_name):
        if service_name == 'ecr':
            return mock_ecr
        return MagicMock()

    mock_boto_client.side_effect = mock_client
    event = {
        'path': '/v1/image-for-docker-runners/sha256:abc123',
        'httpMethod': 'DELETE',
        'pathParameters': {'digest': 'sha256:abc123'}
    }
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


def test_lambda_handler_image_for_docker_runners_unsupported_method_returns_404(v1_handler, image_docker_event_factory, lambda_context):
    event = image_docker_event_factory()
    event['httpMethod'] = 'PUT'
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 404)


def test_lambda_handler_image_for_ec2_runners_post_returns_json_content_type(v1_handler, image_ec2_event_factory, lambda_context):
    event = image_ec2_event_factory(method='POST')
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


@patch('boto3.client')
def test_lambda_handler_image_for_ec2_runners_get_returns_json_content_type(mock_boto_client, v1_handler, image_ec2_event_factory, lambda_context):
    mock_ec2 = MagicMock()
    mock_ec2.describe_images.return_value = {
        'Images': [{
            'ImageId': 'ami-test123',
            'CreationDate': '2024-01-01T00:00:00',
            'Name': 'test-image',
            'State': 'available',
            'Architecture': 'x86_64',
            'Tags': [{'Key': 'stable', 'Value': 'true'}]
        }]
    }

    def mock_client(service_name):
        if service_name == 'ec2':
            return mock_ec2
        return MagicMock()

    mock_boto_client.side_effect = mock_client
    event = image_ec2_event_factory(method='GET', ami_id=None)
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


def test_lambda_handler_image_for_ec2_runners_delete_without_ami_id_returns_400(v1_handler, lambda_context):
    event = {
        'path': '/v1/image-for-ec2-runners/ami-abc123',
        'httpMethod': 'DELETE',
        'pathParameters': {}
    }
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


@patch('boto3.client')
def test_lambda_handler_image_for_ec2_runners_delete_returns_json_content_type(mock_boto_client, v1_handler, lambda_context):
    mock_ec2 = MagicMock()
    mock_ec2.deregister_image.return_value = {}
    mock_ec2.describe_images.return_value = {
        'Images': [{'BlockDeviceMappings': [{'Ebs': {'SnapshotId': 'snap-123'}}]}]
    }
    mock_ec2.delete_snapshot.return_value = {}

    def mock_client(service_name):
        if service_name == 'ec2':
            return mock_ec2
        return MagicMock()

    mock_boto_client.side_effect = mock_client
    event = {
        'path': '/v1/image-for-ec2-runners/ami-abc123',
        'httpMethod': 'DELETE',
        'pathParameters': {'ami_id': 'ami-abc123'}
    }
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


def test_lambda_handler_image_for_ec2_runners_unsupported_method_returns_404(v1_handler, image_ec2_event_factory, lambda_context):
    event = image_ec2_event_factory(ami_id=None)
    event['httpMethod'] = 'PATCH'
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 404)


def test_webhook_router_fixture_sets_api_key_parameter_name(webhook_router):
    assert hasattr(webhook_router, 'lambda_handler') and os.environ['API_KEY_PARAMETER_NAME']


def test_lambda_handler_health_check_returns_200(webhook_router, lambda_context):
    event = {'path': '/v1/runners/health', 'httpMethod': 'GET'}
    response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_health_check_returnscircuit_breaker_state(webhook_router, lambda_context):
    event = {'path': '/v1/runners/health', 'httpMethod': 'GET'}
    response = webhook_router.lambda_handler(event, lambda_context)
    body = parse_response_body(response)
    assert 'circuit_breaker' in body


def test_lambda_handler_health_check_returns_healthy_status(webhook_router, lambda_context):
    event = {'path': '/v1/runners/health', 'httpMethod': 'GET'}
    response = webhook_router.lambda_handler(event, lambda_context)
    body = parse_response_body(response)
    assert body['status'] == 'healthy'


def test_lambda_handler_with_invalid_json_returns_400(webhook_router, lambda_context):
    event = {'path': '/v1/runners', 'httpMethod': 'POST', 'body': 'invalid json', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_lambda_handler_workflow_job_queued_action_returns_200(webhook_router, workflow_job_event_factory, mock_sqs, lambda_context):
    mock_sqs.send_message.return_value = {'MessageId': 'test-message-id'}
    mock_sqs.get_queue_attributes.return_value = {'Attributes': {'ApproximateNumberOfMessages': '5'}}
    event = workflow_job_event_factory(action='queued', labels=['ephemeral-ec2-spot-instance'])
    with patch.object(webhook_router, 'verify_signature', return_value=True):
        with patch.dict('os.environ', {'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'}):
            response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_workflow_job_non_queued_action_returns_200(webhook_router, workflow_job_event_factory, lambda_context):
    event = workflow_job_event_factory(action='completed', labels=['ephemeral-ec2-spot-instance'])
    with patch.object(webhook_router, 'verify_signature', return_value=True):
        with patch('boto3.client'):
            response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_workflow_job_without_matching_labels_returns_200(webhook_router, workflow_job_event_factory, lambda_context):
    event = workflow_job_event_factory(action='queued', labels=['some-other-label'])
    with patch.object(webhook_router, 'verify_signature', return_value=True):
        with patch('boto3.client'):
            response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_ping_event_returns_200(webhook_router, lambda_context):
    event = {
        'path': '/v1/runners',
        'httpMethod': 'POST',
        'body': json.dumps({'zen': 'Design for failure.', 'hook_id': 123}),
        'headers': {'x-github-event': 'ping'}
    }
    with patch('boto3.client'):
        response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


@patch('urllib.request.urlopen')
@patch('boto3.client')
def test_lambda_handler_sqs_event_processes_successfully(mock_boto_client, mock_urlopen, webhook_router, sqs_event_factory, lambda_context):
    mock_ec2 = MagicMock()
    mock_ec2.describe_images.return_value = {
        'Images': [{'ImageId': 'ami-test123', 'CreationDate': '2024-01-01'}]
    }
    mock_ec2.run_instances.return_value = {'Instances': [{'InstanceId': 'i-test123'}]}
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}

    def mock_client(service_name):
        if service_name == 'ec2':
            return mock_ec2
        if service_name == 'ssm':
            return mock_ssm
        return MagicMock()

    mock_boto_client.side_effect = mock_client

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b'{"success": true}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    event = sqs_event_factory(records=[{
        'messageId': 'test-message-id',
        'eventSource': 'aws:sqs',
        'body': json.dumps({'job_id': 123, 'job_labels': ['ephemeral-ec2-spot-instance'], 'github_repo': '10U-Labs-LLC/10ulabs.com'}),
        'attributes': {},
        'messageAttributes': {}
    }])
    response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_verify_signature_with_valid_signature_returns_true(webhook_router):
    secret = 'test-secret'
    payload = 'test payload'
    signature = webhook_router.hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        webhook_router.hashlib.sha256
    ).hexdigest()
    header = f'sha256={signature}'
    result = webhook_router.verify_signature(payload, header, secret)
    assert result is True


def test_verify_signature_with_invalid_signature_returns_false(webhook_router):
    secret = 'test-secret'
    payload = 'test payload'
    header = 'sha256=invalid'
    result = webhook_router.verify_signature(payload, header, secret)
    assert result is False


def test_verify_signature_with_empty_header_returns_false(webhook_router):
    result = webhook_router.verify_signature('payload', '', 'secret')
    assert result is False


def test_verify_signature_with_malformed_header_returns_false(webhook_router):
    result = webhook_router.verify_signature('payload', 'malformed', 'secret')
    assert result is False


def test_check_circuit_breaker_closed_state_returns_true(webhook_router):
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    with patch('boto3.client'):
        result = webhook_router.check_circuit_breaker()
    assert result is True


def test_check_circuit_breaker_open_state_returns_false(webhook_router):
    webhook_router.circuit_breaker_state['state'] = 'open'
    webhook_router.circuit_breaker_state['last_failure_time'] = time.time()
    with patch('boto3.client'):
        result = webhook_router.check_circuit_breaker()
    assert result is False


def test_check_circuit_breaker_transitions_to_half_open_after_timeout(webhook_router):
    webhook_router.circuit_breaker_state['state'] = 'open'
    webhook_router.circuit_breaker_state['last_failure_time'] = time.time() - 61
    with patch('boto3.client'):
        result = webhook_router.check_circuit_breaker()
    assert result is True


def test_check_circuit_breaker_opens_after_threshold_failures(webhook_router):
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 5
    with patch('boto3.client'):
        result = webhook_router.check_circuit_breaker()
    assert result is False


def test_record_circuit_breaker_success_resets_failures(webhook_router):
    webhook_router.circuit_breaker_state['failures'] = 3
    webhook_router.record_circuit_breaker_success()
    assert webhook_router.circuit_breaker_state['failures'] == 0


def test_record_circuit_breaker_success_closes_half_open_circuit(webhook_router):
    webhook_router.circuit_breaker_state['state'] = 'half-open'
    webhook_router.record_circuit_breaker_success()
    assert webhook_router.circuit_breaker_state['state'] == 'closed'


def test_record_circuit_breaker_failure_increments_count(webhook_router):
    webhook_router.circuit_breaker_state['failures'] = 0
    webhook_router.record_circuit_breaker_failure()
    assert webhook_router.circuit_breaker_state['failures'] == 1


def test_record_circuit_breaker_failure_reopens_half_open_circuit(webhook_router):
    webhook_router.circuit_breaker_state['state'] = 'half-open'
    webhook_router.record_circuit_breaker_failure()
    assert webhook_router.circuit_breaker_state['state'] == 'open'


def test_check_and_record_idempotency_with_new_request_returns_false(webhook_router):
    result = webhook_router.check_and_record_idempotency('test-request-id')
    assert result is False


def test_check_and_record_idempotency_with_duplicate_request_returns_true(webhook_router):
    with patch('boto3.client') as mock_boto:
        mock_dynamodb = MagicMock()
        mock_boto.return_value = mock_dynamodb
        error = ClientError({'Error': {'Code': 'ConditionalCheckFailedException'}}, 'PutItem')
        mock_dynamodb.put_item.side_effect = error
        with patch.dict('os.environ', {'IDEMPOTENCY_TABLE_NAME': 'test-table'}):
            result = webhook_router.check_and_record_idempotency('duplicate-id')
    assert result is True


def test_enqueue_job_succeeds_and_returns_message_id(webhook_router, mock_sqs):
    mock_sqs.send_message.return_value = {'MessageId': 'msg-123'}
    mock_sqs.get_queue_attributes.return_value = {
        'Attributes': {'ApproximateNumberOfMessages': '5'}
    }
    with patch.dict('os.environ', {'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'}):
        result = webhook_router.enqueue_job({'job_id': 123})
    assert result['success'] is True


def test_enqueue_job_returns_error_when_queue_url_not_set(webhook_router):
    with patch.dict('os.environ', {}, clear=True):
        result = webhook_router.enqueue_job({'job_id': 123})
    assert result['success'] is False


def test_route_runner_request_with_ec2_label_calls_ec2_endpoint(webhook_router):
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    with patch('boto3.client'), patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'success': True}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = webhook_router.route_runner_request(123, ['ephemeral-ec2-spot-instance'], 'test/repo')
    assert result['success'] is True


def test_route_runner_request_with_fargate_label_calls_docker_endpoint(webhook_router):
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    with patch('boto3.client'), patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'success': True}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = webhook_router.route_runner_request(123, ['ephemeral-ecs-fargate-spot'], 'test/repo')
    assert result['success'] is True


def test_route_runner_request_with_no_matching_labels_returns_error(webhook_router):
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    with patch('boto3.client'):
        result = webhook_router.route_runner_request(123, ['other-label'], 'test/repo')
    assert result['success'] is False


def test_route_runner_request_rejected_when_circuit_breaker_open(webhook_router):
    webhook_router.circuit_breaker_state['state'] = 'open'
    webhook_router.circuit_breaker_state['last_failure_time'] = time.time()
    with patch('boto3.client'):
        result = webhook_router.route_runner_request(123, ['ephemeral-ec2-spot-instance'], 'test/repo')
    assert result['success'] is False


def test_handle_workflow_job_enqueues_ec2_job(webhook_router, mock_sqs):
    event_data = {
        'action': 'queued',
        'workflow_job': {
            'id': 123,
            'name': 'test',
            'labels': ['ephemeral-ec2-spot-instance'],
            'status': 'queued'
        },
        'repository': {'full_name': 'test/repo'}
    }
    mock_sqs.send_message.return_value = {'MessageId': 'msg-123'}
    mock_sqs.get_queue_attributes.return_value = {
        'Attributes': {'ApproximateNumberOfMessages': '0'}
    }
    with patch.dict('os.environ', {'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'}):
        result = webhook_router.handle_workflow_job(event_data)
    assert result['statusCode'] == 200


def test_handle_workflow_job_enqueues_fargate_job(webhook_router, mock_sqs):
    event_data = {
        'action': 'queued',
        'workflow_job': {
            'id': 456,
            'name': 'test',
            'labels': ['ephemeral-ecs-fargate-spot'],
            'status': 'queued'
        },
        'repository': {'full_name': 'test/repo'}
    }
    mock_sqs.send_message.return_value = {'MessageId': 'msg-456'}
    mock_sqs.get_queue_attributes.return_value = {
        'Attributes': {'ApproximateNumberOfMessages': '0'}
    }
    with patch.dict('os.environ', {'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'}):
        result = webhook_router.handle_workflow_job(event_data)
    assert result['statusCode'] == 200


def test_handle_sqs_message_processes_valid_message(webhook_router):
    message = {
        'body': json.dumps({
            'job_id': 123,
            'job_labels': ['ephemeral-ec2-spot-instance'],
            'github_repo': 'test/repo'
        })
    }
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    with patch('boto3.client'), patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'success': True}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = webhook_router.handle_sqs_message(message)
    assert result['success'] is True


def test_handle_sqs_message_with_invalid_json_returns_error(webhook_router):
    message = {'body': 'invalid json'}
    result = webhook_router.handle_sqs_message(message)
    assert result['success'] is False


def test_parse_event_body_with_json_string_returns_dict(webhook_router):
    event = {'body': json.dumps({'key': 'value'})}
    _body_str, payload = webhook_router.parse_event_body(event)
    assert payload['key'] == 'value'


def test_parse_event_body_with_base64_encoded_body_decodes_correctly(webhook_router):
    body = json.dumps({'key': 'value'})
    encoded = base64.b64encode(body.encode()).decode()
    event = {'body': encoded, 'isBase64Encoded': True}
    _body_str, payload = webhook_router.parse_event_body(event)
    assert payload['key'] == 'value'


def test_parse_event_body_with_form_urlencoded_payload_parses_correctly(webhook_router):
    payload = {'key': 'value'}
    encoded = 'payload=' + urllib.parse.quote(json.dumps(payload))
    event = {'body': encoded}
    _body_str, parsed_payload = webhook_router.parse_event_body(event)
    assert parsed_payload['key'] == 'value'


def test_get_webhook_secret_retrieves_from_ssm(webhook_router, mock_ssm):
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': 'test-secret'}
    }
    secret = webhook_router.get_webhook_secret()
    assert secret == 'test-secret'


def test_getwebhook_secret_caches_value(webhook_router, mock_ssm):
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': 'test-secret'}
    }
    webhook_router.get_webhook_secret()
    webhook_router.get_webhook_secret()
    assert mock_ssm.get_parameter.call_count == 1


def test_get_webhook_secret_force_refresh_clears_cache(webhook_router, mock_ssm):
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': 'test-secret'}
    }
    webhook_router.webhook_secret_cache['value'] = 'old-secret'
    secret = webhook_router.get_webhook_secret(force_refresh=True)
    assert secret == 'test-secret'


def test_make_http_request_with_retry_succeeds_on_first_attempt(webhook_router):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'result': 'success'}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        success, _data, _error = webhook_router.make_http_request_with_retry('http://test.com', {})
    assert success is True


def test_make_http_request_with_retry_retries_on_server_error(webhook_router):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 500, 'Server Error', {}, None)
        success, _data, _error = webhook_router.make_http_request_with_retry('http://test.com', {}, max_retries=1)
    assert success is False


def test_make_http_request_with_retry_fails_immediately_on_client_error(webhook_router):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 400, 'Bad Request', {}, None)
        success, _data, _error = webhook_router.make_http_request_with_retry('http://test.com', {})
    assert success is False


def test_publish_metric_sends_to_cloudwatch(webhook_router, mock_cloudwatch):
    webhook_router.publish_metric('TestMetric', 1.0, 'Count')
    assert mock_cloudwatch.put_metric_data.call_count == 1


def test_verify_webhook_signature_with_valid_signature_returns_empty_dict(webhook_router, mock_ssm):
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': 'test-secret'}
    }
    webhook_router.webhook_secret_cache['value'] = None
    payload = 'test payload'
    signature = webhook_router.hmac.new(
        'test-secret'.encode('utf-8'),
        payload.encode('utf-8'),
        webhook_router.hashlib.sha256
    ).hexdigest()
    header = f'sha256={signature}'
    result = webhook_router.verify_webhook_signature(payload, header)
    assert result == {}


def test_verify_webhook_signature_with_invalid_signature_returns_401(webhook_router, mock_ssm):
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': 'test-secret'}
    }
    webhook_router.webhook_secret_cache['value'] = None
    result = webhook_router.verify_webhook_signature('payload', 'sha256=invalid')
    assert result['statusCode'] == 401


def test_handle_api_gateway_event_with_workflow_job_processes_correctly(webhook_router):
    event = {
        'path': '/v1/runners',
        'body': json.dumps({
            'action': 'queued',
            'workflow_job': {
                'id': 123,
                'name': 'test',
                'labels': ['ephemeral-ec2-spot-instance'],
                'status': 'queued'
            },
            'repository': {'full_name': 'test/repo'}
        }),
        'headers': {'x-github-event': 'workflow_job'}
    }
    webhook_router.clients = {'ssm': None, 'dynamodb': None, 'sqs': None, 'cloudwatch': None}
    with patch('boto3.client') as mock_boto:
        mock_sqs = MagicMock()
        mock_boto.return_value = mock_sqs
        mock_sqs.send_message.return_value = {'MessageId': 'msg-123'}
        mock_sqs.get_queue_attributes.return_value = {
            'Attributes': {'ApproximateNumberOfMessages': '0'}
        }
        with patch.dict('os.environ', {'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'}):
            result = webhook_router.handle_api_gateway_event(event, time.time())
    assert result['statusCode'] == 200


def test_lambda_handler_sqs_event_with_failed_message_raises_error(webhook_router, lambda_context):
    event = {
        'Records': [
            {
                'eventSource': 'aws:sqs',
                'body': 'invalid json'
            }
        ]
    }
    with pytest.raises(RuntimeError):
        webhook_router.lambda_handler(event, lambda_context)



def test_handler_checks_circuit_breaker_health(circuit_breaker_remediation, lambda_context):
    event = {}
    with patch.dict(os.environ, {'WEBHOOK_FUNCTION_NAME': 'test-function'}):
        with patch('boto3.client') as mock_boto_client:
            mock_lambda = MagicMock()
            mock_boto_client.return_value = mock_lambda
            mock_lambda.invoke.return_value = {
                'Payload': MagicMock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({'circuit_breaker_state': 'closed'})
                }).encode())
            }
            response = circuit_breaker_remediation.handler(event, lambda_context)
    assert_response_status(response, 200)


def test_handler_returnscircuit_breaker_state(circuit_breaker_remediation, lambda_context):
    event = {}
    with patch.dict(os.environ, {'WEBHOOK_FUNCTION_NAME': 'test-function'}):
        with patch('boto3.client') as mock_boto_client:
            mock_lambda = MagicMock()
            mock_boto_client.return_value = mock_lambda
            mock_lambda.invoke.return_value = {
                'Payload': MagicMock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({'circuit_breaker_state': 'closed'})
                }).encode())
            }
            response = circuit_breaker_remediation.handler(event, lambda_context)
            body = parse_response_body(response)
    assert 'circuit_breaker_state' in body


def test_handler_monitors_open_circuit_breaker(circuit_breaker_remediation, lambda_context):
    event = {}
    with patch.dict(os.environ, {'WEBHOOK_FUNCTION_NAME': 'test-function'}):
        with patch('boto3.client') as mock_boto_client:
            mock_lambda = MagicMock()
            mock_boto_client.return_value = mock_lambda
            mock_lambda.invoke.return_value = {
                'Payload': MagicMock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({'circuit_breaker_state': 'open'})
                }).encode())
            }
            response = circuit_breaker_remediation.handler(event, lambda_context)
            body = parse_response_body(response)
    assert body['action'] == 'monitored'


def test_handler_does_nothing_for_closed_circuit(circuit_breaker_remediation, lambda_context):
    event = {}
    with patch.dict(os.environ, {'WEBHOOK_FUNCTION_NAME': 'test-function'}):
        with patch('boto3.client') as mock_boto_client:
            mock_lambda = MagicMock()
            mock_boto_client.return_value = mock_lambda
            mock_lambda.invoke.return_value = {
                'Payload': MagicMock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({'circuit_breaker_state': 'closed'})
                }).encode())
            }
            response = circuit_breaker_remediation.handler(event, lambda_context)
            body = parse_response_body(response)
    assert body['action'] == 'none'


def test_handler_returns_500_when_function_name_not_set(circuit_breaker_remediation, lambda_context):
    event = {}
    with patch.dict('os.environ', {}, clear=True):
        response = circuit_breaker_remediation.handler(event, lambda_context)
    assert_response_status(response, 500)


def test_check_circuit_breaker_health_invokes_lambda(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_boto_client.return_value = mock_lambda
        mock_lambda.invoke.return_value = {
            'Payload': MagicMock(read=lambda: json.dumps({
                'statusCode': 200,
                'body': json.dumps({'circuit_breaker_state': 'closed'})
            }).encode())
        }
        circuit_breaker_remediation.check_circuit_breaker_health('test-function')
    assert mock_lambda.invoke.called


def test_check_circuit_breaker_health_returns_state(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_boto_client.return_value = mock_lambda
        mock_lambda.invoke.return_value = {
            'Payload': MagicMock(read=lambda: json.dumps({
                'statusCode': 200,
                'body': json.dumps({'circuit_breaker_state': 'closed'})
            }).encode())
        }
        result = circuit_breaker_remediation.check_circuit_breaker_health('test-function')
    assert result['circuit_breaker_state'] == 'closed'


def test_check_circuit_breaker_health_handles_non_200_response(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_boto_client.return_value = mock_lambda
        mock_lambda.invoke.return_value = {
            'Payload': MagicMock(read=lambda: json.dumps({
                'statusCode': 500,
                'body': json.dumps({'error': 'Internal error'})
            }).encode())
        }
        result = circuit_breaker_remediation.check_circuit_breaker_health('test-function')
    assert result['circuit_breaker_state'] == 'unknown'


def test_check_circuit_breaker_health_handles_lambda_error(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_boto_client.return_value = mock_lambda
        mock_lambda.invoke.side_effect = ClientError(
            {'Error': {'Code': 'FunctionNotFound'}},
            'Invoke'
        )
        result = circuit_breaker_remediation.check_circuit_breaker_health('test-function')
    assert result['circuit_breaker_state'] == 'unknown'


def test_check_circuit_breaker_health_includes_error_message(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_boto_client.return_value = mock_lambda
        mock_lambda.invoke.side_effect = ClientError(
            {'Error': {'Code': 'FunctionNotFound'}},
            'Invoke'
        )
        result = circuit_breaker_remediation.check_circuit_breaker_health('test-function')
    assert 'error' in result


def test_handler_processes_job_dlq(dlq_reprocessor, dlq_message_factory, mock_sqs, lambda_context):
    event = {}
    mock_sqs.receive_message.return_value = {
        'Messages': [dlq_message_factory(body={'job_id': 123})]
    }
    with patch.dict('os.environ', {
        'JOB_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/job-dlq',
        'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/job-queue'
    }):
        response = dlq_reprocessor.handler(event, lambda_context)
    assert_response_status(response, 200)


def test_handler_returns_reprocessed_count(dlq_reprocessor, dlq_message_factory, mock_sqs, lambda_context):
    event = {}
    mock_sqs.receive_message.return_value = {
        'Messages': [dlq_message_factory(body={'job_id': 123})]
    }
    with patch.dict('os.environ', {
        'JOB_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/job-dlq',
        'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/job-queue'
    }):
        response = dlq_reprocessor.handler(event, lambda_context)
        body = parse_response_body(response)
    assert body['job_dlq']['reprocessed'] == 1


def test_handler_handles_webhook_dlq_with_note(dlq_reprocessor, lambda_context):
    event = {}
    with patch.dict('os.environ', {
        'WEBHOOK_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/webhook-dlq'
    }):
        response = dlq_reprocessor.handler(event, lambda_context)
        body = parse_response_body(response)
    assert 'note' in body['webhook_dlq']


def test_handler_skips_job_dlq_when_not_configured(dlq_reprocessor, lambda_context):
    event = {}
    with patch.dict('os.environ', {}, clear=True):
        response = dlq_reprocessor.handler(event, lambda_context)
        body = parse_response_body(response)
    assert 'job_dlq' not in body


def test_handler_skips_webhook_dlq_when_not_configured(dlq_reprocessor, lambda_context):
    event = {}
    with patch.dict('os.environ', {}, clear=True):
        response = dlq_reprocessor.handler(event, lambda_context)
        body = parse_response_body(response)
    assert 'webhook_dlq' not in body


def test_reprocess_dlq_messages_receives_messages(dlq_reprocessor, mock_sqs):
    mock_sqs.receive_message.return_value = {
        'Messages': [
            {
                'Body': json.dumps({'test': 'data'}),
                'ReceiptHandle': 'receipt-1',
                'MessageAttributes': {}
            }
        ]
    }
    result = dlq_reprocessor.reprocess_dlq_messages(
        'https://sqs.us-east-1.amazonaws.com/123456789012/dlq',
        'https://sqs.us-east-1.amazonaws.com/123456789012/target'
    )
    assert result['reprocessed'] == 1


def test_reprocess_dlq_messages_sends_to_target_queue(dlq_reprocessor, mock_sqs):
    mock_sqs.receive_message.return_value = {
        'Messages': [
            {
                'Body': json.dumps({'test': 'data'}),
                'ReceiptHandle': 'receipt-1',
                'MessageAttributes': {}
            }
        ]
    }
    dlq_reprocessor.reprocess_dlq_messages(
        'https://sqs.us-east-1.amazonaws.com/123456789012/dlq',
        'https://sqs.us-east-1.amazonaws.com/123456789012/target'
    )
    assert mock_sqs.send_message.called


def test_reprocess_dlq_messages_deletes_from_dlq(dlq_reprocessor, mock_sqs):
    mock_sqs.receive_message.return_value = {
        'Messages': [
            {
                'Body': json.dumps({'test': 'data'}),
                'ReceiptHandle': 'receipt-1',
                'MessageAttributes': {}
            }
        ]
    }
    dlq_reprocessor.reprocess_dlq_messages(
        'https://sqs.us-east-1.amazonaws.com/123456789012/dlq',
        'https://sqs.us-east-1.amazonaws.com/123456789012/target'
    )
    assert mock_sqs.delete_message.called


def test_reprocess_dlq_messages_handles_empty_queue(dlq_reprocessor, mock_sqs):
    mock_sqs.receive_message.return_value = {}
    result = dlq_reprocessor.reprocess_dlq_messages(
        'https://sqs.us-east-1.amazonaws.com/123456789012/dlq',
        'https://sqs.us-east-1.amazonaws.com/123456789012/target'
    )
    assert result['reprocessed'] == 0


def test_reprocess_dlq_messages_processes_multiple_messages(dlq_reprocessor, mock_sqs):
    mock_sqs.receive_message.return_value = {
        'Messages': [
            {
                'Body': json.dumps({'id': 1}),
                'ReceiptHandle': 'receipt-1',
                'MessageAttributes': {}
            },
            {
                'Body': json.dumps({'id': 2}),
                'ReceiptHandle': 'receipt-2',
                'MessageAttributes': {}
            },
            {
                'Body': json.dumps({'id': 3}),
                'ReceiptHandle': 'receipt-3',
                'MessageAttributes': {}
            }
        ]
    }
    result = dlq_reprocessor.reprocess_dlq_messages(
        'https://sqs.us-east-1.amazonaws.com/123456789012/dlq',
        'https://sqs.us-east-1.amazonaws.com/123456789012/target'
    )
    assert result['reprocessed'] == 3


def test_reprocess_dlq_messages_counts_failures(dlq_reprocessor, mock_sqs):
    mock_sqs.receive_message.return_value = {
        'Messages': [
            {
                'Body': json.dumps({'id': 1}),
                'ReceiptHandle': 'receipt-1',
                'MessageAttributes': {}
            }
        ]
    }
    mock_sqs.send_message.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable'}},
        'SendMessage'
    )
    result = dlq_reprocessor.reprocess_dlq_messages(
        'https://sqs.us-east-1.amazonaws.com/123456789012/dlq',
        'https://sqs.us-east-1.amazonaws.com/123456789012/target'
    )
    assert result['failed'] == 1


def test_reprocess_dlq_messages_respects_max_messages_limit(dlq_reprocessor, mock_sqs):
    mock_sqs.receive_message.return_value = {
        'Messages': [
            {
                'Body': json.dumps({'id': i}),
                'ReceiptHandle': f'receipt-{i}',
                'MessageAttributes': {}
            }
            for i in range(5)
        ]
    }
    dlq_reprocessor.reprocess_dlq_messages(
        'https://sqs.us-east-1.amazonaws.com/123456789012/dlq',
        'https://sqs.us-east-1.amazonaws.com/123456789012/target',
        max_messages=5
    )
    call_args = mock_sqs.receive_message.call_args
    assert call_args[1]['MaxNumberOfMessages'] == 5


def test_reprocess_dlq_messages_preserves_message_attributes(dlq_reprocessor, mock_sqs):
    mock_sqs.receive_message.return_value = {
        'Messages': [
            {
                'Body': json.dumps({'id': 1}),
                'ReceiptHandle': 'receipt-1',
                'MessageAttributes': {'key': {'StringValue': 'value', 'DataType': 'String'}}
            }
        ]
    }
    dlq_reprocessor.reprocess_dlq_messages(
        'https://sqs.us-east-1.amazonaws.com/123456789012/dlq',
        'https://sqs.us-east-1.amazonaws.com/123456789012/target'
    )
    call_args = mock_sqs.send_message.call_args
    assert 'MessageAttributes' in call_args[1]


def test_reprocess_dlq_messages_handles_receive_error(dlq_reprocessor, mock_sqs):
    mock_sqs.receive_message.side_effect = ClientError(
        {'Error': {'Code': 'QueueDoesNotExist'}},
        'ReceiveMessage'
    )
    result = dlq_reprocessor.reprocess_dlq_messages(
        'https://sqs.us-east-1.amazonaws.com/123456789012/dlq',
        'https://sqs.us-east-1.amazonaws.com/123456789012/target'
    )
    assert 'error' in result


def test_reprocess_dlq_messages_continues_on_individual_failure(dlq_reprocessor, mock_sqs):
    mock_sqs.receive_message.return_value = {
        'Messages': [
            {
                'Body': json.dumps({'id': 1}),
                'ReceiptHandle': 'receipt-1',
                'MessageAttributes': {}
            },
            {
                'Body': json.dumps({'id': 2}),
                'ReceiptHandle': 'receipt-2',
                'MessageAttributes': {}
            }
        ]
    }
    mock_sqs.send_message.side_effect = [
        ClientError({'Error': {'Code': 'ServiceUnavailable'}}, 'SendMessage'),
        {'MessageId': 'msg-2'}
    ]
    result = dlq_reprocessor.reprocess_dlq_messages(
        'https://sqs.us-east-1.amazonaws.com/123456789012/dlq',
        'https://sqs.us-east-1.amazonaws.com/123456789012/target'
    )
    assert result['reprocessed'] == 1


def test_reprocess_dlq_messages_uses_long_polling(dlq_reprocessor, mock_sqs):
    mock_sqs.receive_message.return_value = {}
    dlq_reprocessor.reprocess_dlq_messages(
        'https://sqs.us-east-1.amazonaws.com/123456789012/dlq',
        'https://sqs.us-east-1.amazonaws.com/123456789012/target'
    )
    call_args = mock_sqs.receive_message.call_args
    assert call_args[1]['WaitTimeSeconds'] == 5


def test_get_docker_runner_status_returns_success_with_no_tasks(v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(v1_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.return_value = {'taskArns': []}
            mock_get_client.return_value = mock_ecs

            result = v1_handler.get_docker_runner_status()

            assert result['success'] is True


def test_get_docker_runner_status_returns_zero_running_tasks_when_empty(v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(v1_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.return_value = {'taskArns': []}
            mock_get_client.return_value = mock_ecs

            result = v1_handler.get_docker_runner_status()

            assert result['running_tasks'] == 0


def test_get_docker_runner_status_returns_empty_task_list_when_no_tasks(v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(v1_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.return_value = {'taskArns': []}
            mock_get_client.return_value = mock_ecs

            result = v1_handler.get_docker_runner_status()

            assert result['tasks'] == []


def test_get_docker_runner_status_returns_cluster_name(v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(v1_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.return_value = {'taskArns': []}
            mock_get_client.return_value = mock_ecs

            result = v1_handler.get_docker_runner_status()

            assert result['cluster'] == 'test-cluster'


def test_get_docker_runner_status_handles_client_error(v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(v1_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.side_effect = ClientError(
                {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
                'list_tasks'
            )
            mock_get_client.return_value = mock_ecs

            result = v1_handler.get_docker_runner_status()

            assert result['success'] is False


def test_get_ec2_runner_status_returns_success_with_no_instances(v1_handler):
    with patch.object(v1_handler, 'get_ec2_client') as mock_get_client:
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {'Reservations': []}
        mock_get_client.return_value = mock_ec2

        result = v1_handler.get_ec2_runner_status()

        assert result['success'] is True


def test_get_ec2_runner_status_returns_zero_running_instances_when_empty(v1_handler):
    with patch.object(v1_handler, 'get_ec2_client') as mock_get_client:
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {'Reservations': []}
        mock_get_client.return_value = mock_ec2

        result = v1_handler.get_ec2_runner_status()

        assert result['running_instances'] == 0


def test_get_ec2_runner_status_returns_empty_instance_list_when_none_running(v1_handler):
    with patch.object(v1_handler, 'get_ec2_client') as mock_get_client:
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {'Reservations': []}
        mock_get_client.return_value = mock_ec2

        result = v1_handler.get_ec2_runner_status()

        assert result['instances'] == []


def test_get_ec2_runner_status_handles_client_error(v1_handler):
    with patch.object(v1_handler, 'get_ec2_client') as mock_get_client:
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.side_effect = ClientError(
            {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
            'describe_instances'
        )
        mock_get_client.return_value = mock_ec2

        result = v1_handler.get_ec2_runner_status()

        assert result['success'] is False


def test_handle_docker_runner_get_returns_200_status(v1_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'GET'}
    with patch.object(v1_handler, 'get_docker_runner_status') as mock_status:
        mock_status.return_value = {'success': True, 'running_tasks': 0, 'tasks': [], 'cluster': 'test'}
        response = v1_handler.lambda_handler(event, lambda_context)

        assert_response_status(response, 200)


def test_handle_docker_runner_get_returns_json_content_type(v1_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'GET'}
    with patch.object(v1_handler, 'get_docker_runner_status') as mock_status:
        mock_status.return_value = {'success': True, 'running_tasks': 0, 'tasks': [], 'cluster': 'test'}
        response = v1_handler.lambda_handler(event, lambda_context)

        assert_json_content_type(response)


def test_handle_ec2_runner_get_returns_200_status(v1_handler, lambda_context):
    event = {'path': '/v1/ec2-runner', 'httpMethod': 'GET'}
    with patch.object(v1_handler, 'get_ec2_runner_status') as mock_status:
        mock_status.return_value = {'success': True, 'running_instances': 0, 'instances': []}
        response = v1_handler.lambda_handler(event, lambda_context)

        assert_response_status(response, 200)


def test_handle_ec2_runner_get_returns_json_content_type(v1_handler, lambda_context):
    event = {'path': '/v1/ec2-runner', 'httpMethod': 'GET'}
    with patch.object(v1_handler, 'get_ec2_runner_status') as mock_status:
        mock_status.return_value = {'success': True, 'running_instances': 0, 'instances': []}
        response = v1_handler.lambda_handler(event, lambda_context)

        assert_json_content_type(response)
