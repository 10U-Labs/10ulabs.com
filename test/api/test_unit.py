from pathlib import Path
import json
import os
import time
from unittest.mock import patch, MagicMock
import pytest
from conftest import parse_response_body, assert_response_status, assert_json_content_type, assert_cors_headers


def test_config_file_exists_in_correct_location():
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "config.json"
    assert config_path.exists()


def test_config_has_aws_account_id(config):
    assert "account_id" in config["aws"]


def test_config_has_aws_region(config):
    assert "region" in config["aws"]


def test_config_has_stack_name(config):
    assert "stack_name" in config["naming"]


def test_config_has_subdomain_name(config):
    assert "subdomain" in config["domain_names"]


def test_config_has_parent_domain(config):
    assert "parent" in config["domain_names"]


def test_api_has_lambda_function(cdk_template):
    resources = cdk_template.find_resources("AWS::Lambda::Function")
    assert len(resources) >= 1


def test_api_has_api_gateway(cdk_template):
    cdk_template.resource_count_is("AWS::ApiGateway::RestApi", 1)


def test_api_gateway_has_no_custom_domain(cdk_template):
    cdk_template.resource_count_is("AWS::ApiGateway::DomainName", 0)


def test_api_has_certificate(cdk_template):
    cdk_template.resource_count_is("AWS::CertificateManager::Certificate", 1)


def test_api_has_route53_record(cdk_template):
    cdk_template.resource_count_is("AWS::Route53::RecordSet", 1)


def test_api_has_url_output(cdk_template):
    outputs = cdk_template.find_outputs("*")
    assert "ApiUrl" in outputs


def test_api_has_domain_name_output(cdk_template):
    outputs = cdk_template.find_outputs("*")
    assert "ApiDomainName" in outputs


def test_api_has_endpoint_output(cdk_template):
    outputs = cdk_template.find_outputs("*")
    assert "ApiEndpoint" in outputs


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
    openapi_path = Path(__file__).parent.parent.parent / "src" / "api" / "openapi.yml"
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
    event = docker_runner_post_event_factory(job_id=12345, github_repo='10U-Labs-LLC/10ulabs.com')
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


@patch('boto3.client')
def test_lambda_handler_docker_runner_get_returns_json_content_type(mock_boto_client, v1_handler, lambda_context):
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

    def mock_client(service_name, **kwargs):
        if service_name == 'ec2':
            return mock_ec2
        elif service_name == 'ssm':
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


def test_lambda_handler_health_check_returns_200(webhook_router, lambda_context):
    event = {'path': '/v1/runners/health', 'httpMethod': 'GET'}
    response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_health_check_returns_circuit_breaker_state(webhook_router, lambda_context):
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
    from unittest.mock import patch
    event = workflow_job_event_factory(action='queued', labels=['ephemeral-ec2-spot-instance'])
    with patch.dict('os.environ', {'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'}):
        response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_workflow_job_non_queued_action_returns_200(webhook_router, workflow_job_event_factory, lambda_context):
    from unittest.mock import patch
    event = workflow_job_event_factory(action='completed', labels=['ephemeral-ec2-spot-instance'])
    with patch('boto3.client'):
        response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_workflow_job_without_matching_labels_returns_200(webhook_router, workflow_job_event_factory, lambda_context):
    from unittest.mock import patch
    event = workflow_job_event_factory(action='queued', labels=['some-other-label'])
    with patch('boto3.client'):
        response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_ping_event_returns_200(webhook_router, lambda_context):
    from unittest.mock import patch
    event = {
        'path': '/v1/runners',
        'httpMethod': 'POST',
        'body': json.dumps({'zen': 'Design for failure.', 'hook_id': 123}),
        'headers': {'x-github-event': 'ping'}
    }
    with patch('boto3.client'):
        response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


@patch('boto3.client')
def test_lambda_handler_sqs_event_processes_successfully(mock_boto_client, webhook_router, sqs_event_factory, mock_github_api_success, lambda_context):
    from unittest.mock import MagicMock
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
    webhook_router._circuit_breaker_state['state'] = 'closed'
    webhook_router._circuit_breaker_state['failures'] = 0
    with patch('boto3.client'):
        result = webhook_router.check_circuit_breaker()
    assert result is True


def test_check_circuit_breaker_open_state_returns_false(webhook_router):
    webhook_router._circuit_breaker_state['state'] = 'open'
    webhook_router._circuit_breaker_state['last_failure_time'] = time.time()
    with patch('boto3.client'):
        result = webhook_router.check_circuit_breaker()
    assert result is False


def test_check_circuit_breaker_transitions_to_half_open_after_timeout(webhook_router):
    webhook_router._circuit_breaker_state['state'] = 'open'
    webhook_router._circuit_breaker_state['last_failure_time'] = time.time() - 61
    with patch('boto3.client'):
        result = webhook_router.check_circuit_breaker()
    assert result is True


def test_check_circuit_breaker_opens_after_threshold_failures(webhook_router):
    webhook_router._circuit_breaker_state['state'] = 'closed'
    webhook_router._circuit_breaker_state['failures'] = 5
    with patch('boto3.client'):
        result = webhook_router.check_circuit_breaker()
    assert result is False


def test_record_circuit_breaker_success_resets_failures(webhook_router):
    webhook_router._circuit_breaker_state['failures'] = 3
    webhook_router.record_circuit_breaker_success()
    assert webhook_router._circuit_breaker_state['failures'] == 0


def test_record_circuit_breaker_success_closes_half_open_circuit(webhook_router):
    webhook_router._circuit_breaker_state['state'] = 'half-open'
    webhook_router.record_circuit_breaker_success()
    assert webhook_router._circuit_breaker_state['state'] == 'closed'


def test_record_circuit_breaker_failure_increments_count(webhook_router):
    webhook_router._circuit_breaker_state['failures'] = 0
    webhook_router.record_circuit_breaker_failure()
    assert webhook_router._circuit_breaker_state['failures'] == 1


def test_record_circuit_breaker_failure_reopens_half_open_circuit(webhook_router):
    webhook_router._circuit_breaker_state['state'] = 'half-open'
    webhook_router.record_circuit_breaker_failure()
    assert webhook_router._circuit_breaker_state['state'] == 'open'


def test_check_and_record_idempotency_with_new_request_returns_false(webhook_router, mock_dynamodb):
    result = webhook_router.check_and_record_idempotency('test-request-id')
    assert result is False


def test_check_and_record_idempotency_with_duplicate_request_returns_true(webhook_router):
    from botocore.exceptions import ClientError
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
    webhook_router._circuit_breaker_state['state'] = 'closed'
    webhook_router._circuit_breaker_state['failures'] = 0
    with patch('boto3.client'), patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'success': True}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = webhook_router.route_runner_request(123, ['ephemeral-ec2-spot-instance'], 'test/repo')
    assert result['success'] is True


def test_route_runner_request_with_fargate_label_calls_docker_endpoint(webhook_router):
    webhook_router._circuit_breaker_state['state'] = 'closed'
    webhook_router._circuit_breaker_state['failures'] = 0
    with patch('boto3.client'), patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'success': True}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = webhook_router.route_runner_request(123, ['ephemeral-ecs-fargate-spot'], 'test/repo')
    assert result['success'] is True


def test_route_runner_request_with_no_matching_labels_returns_error(webhook_router):
    webhook_router._circuit_breaker_state['state'] = 'closed'
    webhook_router._circuit_breaker_state['failures'] = 0
    with patch('boto3.client'):
        result = webhook_router.route_runner_request(123, ['other-label'], 'test/repo')
    assert result['success'] is False


def test_route_runner_request_rejected_when_circuit_breaker_open(webhook_router):
    webhook_router._circuit_breaker_state['state'] = 'open'
    webhook_router._circuit_breaker_state['last_failure_time'] = time.time()
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
    webhook_router._circuit_breaker_state['state'] = 'closed'
    webhook_router._circuit_breaker_state['failures'] = 0
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
    body_str, payload = webhook_router.parse_event_body(event)
    assert payload['key'] == 'value'


def test_parse_event_body_with_base64_encoded_body_decodes_correctly(webhook_router):
    import base64
    body = json.dumps({'key': 'value'})
    encoded = base64.b64encode(body.encode()).decode()
    event = {'body': encoded, 'isBase64Encoded': True}
    body_str, payload = webhook_router.parse_event_body(event)
    assert payload['key'] == 'value'


def test_parse_event_body_with_form_urlencoded_payload_parses_correctly(webhook_router):
    import urllib.parse
    payload = {'key': 'value'}
    encoded = 'payload=' + urllib.parse.quote(json.dumps(payload))
    event = {'body': encoded}
    body_str, parsed_payload = webhook_router.parse_event_body(event)
    assert parsed_payload['key'] == 'value'


def test_get_webhook_secret_retrieves_from_ssm(webhook_router, mock_ssm):
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': 'test-secret'}
    }
    secret = webhook_router.get_webhook_secret()
    assert secret == 'test-secret'


def test_get_webhook_secret_caches_value(webhook_router, mock_ssm):
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
    webhook_router._webhook_secret_cache['value'] = 'old-secret'
    secret = webhook_router.get_webhook_secret(force_refresh=True)
    assert secret == 'test-secret'


def test_make_http_request_with_retry_succeeds_on_first_attempt(webhook_router):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'result': 'success'}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        success, data, error = webhook_router.make_http_request_with_retry('http://test.com', {})
    assert success is True


def test_make_http_request_with_retry_retries_on_server_error(webhook_router):
    with patch('urllib.request.urlopen') as mock_urlopen:
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 500, 'Server Error', {}, None)
        success, data, error = webhook_router.make_http_request_with_retry('http://test.com', {}, max_retries=1)
    assert success is False


def test_make_http_request_with_retry_fails_immediately_on_client_error(webhook_router):
    with patch('urllib.request.urlopen') as mock_urlopen:
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 400, 'Bad Request', {}, None)
        success, data, error = webhook_router.make_http_request_with_retry('http://test.com', {})
    assert success is False


def test_publish_metric_sends_to_cloudwatch(webhook_router, mock_cloudwatch):
    webhook_router.publish_metric('TestMetric', 1.0, 'Count')
    assert mock_cloudwatch.put_metric_data.call_count == 1


def test_verify_webhook_signature_with_valid_signature_returns_empty_dict(webhook_router, mock_ssm):
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': 'test-secret'}
    }
    webhook_router._webhook_secret_cache['value'] = None
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
    webhook_router._webhook_secret_cache['value'] = None
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
    webhook_router._clients = {'ssm': None, 'dynamodb': None, 'sqs': None, 'cloudwatch': None}
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


def test_lambda_handler_create_request_creates_webhook(configure_webhook, cfn_event_factory, mock_ssm, lambda_context):
    from unittest.mock import MagicMock, patch
    event = cfn_event_factory(request_type='Create', properties={
        'WebhookUrl': 'https://api.10ulabs.com/v1/runners',
        'Repository': '10U-Labs-LLC/10ulabs.com'
    })
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'id': 12345}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        response = configure_webhook.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_delete_request_deletes_webhook(configure_webhook, cfn_event_factory, mock_ssm, lambda_context):
    from unittest.mock import MagicMock, patch
    event = cfn_event_factory(request_type='Delete', properties={
        'WebhookUrl': 'https://api.10ulabs.com/v1/runners',
        'Repository': '10U-Labs-LLC/10ulabs.com',
        'WebhookId': '12345'
    }, physical_resource_id='github-webhook-10U-Labs-LLC-10ulabs.com')
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        response = configure_webhook.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_update_request_creates_webhook(configure_webhook, cfn_event_factory, mock_ssm, lambda_context):
    from unittest.mock import MagicMock, patch
    event = cfn_event_factory(request_type='Update', properties={
        'WebhookUrl': 'https://api.10ulabs.com/v1/runners',
        'Repository': '10U-Labs-LLC/10ulabs.com'
    })
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'id': 12345}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        response = configure_webhook.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_unsupported_request_type_returns_400(configure_webhook, cfn_event_factory, lambda_context):
    from unittest.mock import patch
    event = cfn_event_factory(request_type='Unknown', properties={})
    with patch('urllib.request.urlopen'):
        response = configure_webhook.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_get_github_pat_retrieves_from_ssm(configure_webhook, mock_ssm):
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': 'github-pat-token'}
    }
    pat = configure_webhook.get_github_pat()
    assert pat == 'github-pat-token'


def test_get_github_pat_handles_ssm_error(configure_webhook, mock_ssm):
    from botocore.exceptions import ClientError
    mock_ssm.get_parameter.side_effect = ClientError(
        {'Error': {'Code': 'ParameterNotFound'}},
        'GetParameter'
    )
    pat = configure_webhook.get_github_pat()
    assert pat == ''


def test_get_or_create_webhook_secret_retrieves_existing_secret(configure_webhook, mock_ssm):
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': 'existing-secret'}
    }
    secret = configure_webhook.get_or_create_webhook_secret()
    assert secret == 'existing-secret'


def test_get_or_create_webhook_secret_creates_new_secret_when_not_found(configure_webhook):
    from botocore.exceptions import ClientError
    configure_webhook._clients = {'ssm': None}
    with patch('boto3.client') as mock_boto:
        mock_ssm = MagicMock()
        mock_boto.return_value = mock_ssm
        param_not_found = type('ParameterNotFound', (ClientError,), {})
        mock_ssm.exceptions.ParameterNotFound = param_not_found
        error = param_not_found(
            {'Error': {'Code': 'ParameterNotFound'}},
            'GetParameter'
        )
        mock_ssm.get_parameter.side_effect = error
        secret = configure_webhook.get_or_create_webhook_secret()
    assert len(secret) > 0


def test_create_github_webhook_succeeds_on_first_attempt(configure_webhook):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'id': 12345}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = configure_webhook.create_github_webhook(
            'https://api.10ulabs.com/v1/runners',
            'secret',
            'pat-token',
            '10U-Labs-LLC/10ulabs.com'
        )
    assert result['success'] is True


def test_create_github_webhook_returns_webhook_id_on_success(configure_webhook):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'id': 12345}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = configure_webhook.create_github_webhook(
            'https://api.10ulabs.com/v1/runners',
            'secret',
            'pat-token',
            '10U-Labs-LLC/10ulabs.com'
        )
    assert result['webhook_id'] == 12345


def test_create_github_webhook_retries_on_server_error(configure_webhook):
    import urllib.error
    with patch('urllib.request.urlopen') as mock_urlopen, patch('time.sleep'):
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 500, 'Server Error', {}, None)
        result = configure_webhook.create_github_webhook(
            'https://api.10ulabs.com/v1/runners',
            'secret',
            'pat-token',
            '10U-Labs-LLC/10ulabs.com'
        )
    assert result['success'] is False


def test_create_github_webhook_does_not_retry_on_client_error(configure_webhook):
    import urllib.error
    error_response = MagicMock()
    error_response.read.return_value = b'Bad Request'
    error_response.fp = error_response
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 400, 'Bad Request', {}, error_response)
        result = configure_webhook.create_github_webhook(
            'https://api.10ulabs.com/v1/runners',
            'secret',
            'pat-token',
            '10U-Labs-LLC/10ulabs.com'
        )
    assert result['success'] is False


def test_create_github_webhook_handles_duplicate_webhook(configure_webhook):
    import urllib.error
    error_response = MagicMock()
    error_response.read.return_value = b'hook already exists on this repository'
    error_response.fp = error_response
    with patch('urllib.request.urlopen') as mock_urlopen:
        list_response = MagicMock()
        list_response.read.return_value = json.dumps([
            {'id': 99999, 'config': {'url': 'https://api.10ulabs.com/v1/runners'}}
        ]).encode()
        list_response.__enter__.return_value = list_response
        mock_urlopen.side_effect = [
            urllib.error.HTTPError('url', 422, 'Unprocessable Entity', {}, error_response),
            list_response
        ]
        result = configure_webhook.create_github_webhook(
            'https://api.10ulabs.com/v1/runners',
            'secret',
            'pat-token',
            '10U-Labs-LLC/10ulabs.com'
        )
    assert result['success'] is True


def test_delete_github_webhook_succeeds(configure_webhook):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = configure_webhook.delete_github_webhook(12345, 'pat-token', '10U-Labs-LLC/10ulabs.com')
    assert result['success'] is True


def test_delete_github_webhook_handles_404_as_success(configure_webhook):
    import urllib.error
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 404, 'Not Found', {}, None)
        result = configure_webhook.delete_github_webhook(12345, 'pat-token', '10U-Labs-LLC/10ulabs.com')
    assert result['success'] is True


def test_delete_github_webhook_retries_on_server_error(configure_webhook):
    import urllib.error
    with patch('urllib.request.urlopen') as mock_urlopen, patch('time.sleep'):
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 500, 'Server Error', {}, None)
        result = configure_webhook.delete_github_webhook(12345, 'pat-token', '10U-Labs-LLC/10ulabs.com')
    assert result['success'] is False


def test_delete_github_webhook_does_not_retry_on_client_error(configure_webhook):
    import urllib.error
    error_response = MagicMock()
    error_response.read.return_value = b'Bad Request'
    error_response.fp = error_response
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 400, 'Bad Request', {}, error_response)
        result = configure_webhook.delete_github_webhook(12345, 'pat-token', '10U-Labs-LLC/10ulabs.com')
    assert result['success'] is False


def test_list_github_webhooks_returns_webhooks(configure_webhook):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {'id': 1, 'config': {'url': 'https://example.com'}},
            {'id': 2, 'config': {'url': 'https://example2.com'}}
        ]).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = configure_webhook.list_github_webhooks('pat-token', '10U-Labs-LLC/10ulabs.com')
    assert result['success'] is True


def test_list_github_webhooks_returns_webhook_count(configure_webhook):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {'id': 1, 'config': {'url': 'https://example.com'}},
            {'id': 2, 'config': {'url': 'https://example2.com'}}
        ]).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = configure_webhook.list_github_webhooks('pat-token', '10U-Labs-LLC/10ulabs.com')
    assert len(result['webhooks']) == 2


def test_list_github_webhooks_handles_http_error(configure_webhook):
    import urllib.error
    error_response = MagicMock()
    error_response.read.return_value = b'Unauthorized'
    error_response.fp = error_response
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 401, 'Unauthorized', {}, error_response)
        result = configure_webhook.list_github_webhooks('pat-token', '10U-Labs-LLC/10ulabs.com')
    assert result['success'] is False


def test_handle_duplicate_webhook_finds_existing_webhook(configure_webhook):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {'id': 12345, 'config': {'url': 'https://api.10ulabs.com/v1/runners'}}
        ]).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = configure_webhook.handle_duplicate_webhook(
            'https://api.10ulabs.com/v1/runners',
            'pat-token',
            '10U-Labs-LLC/10ulabs.com'
        )
    assert result['success'] is True


def test_handle_duplicate_webhook_returns_webhook_id(configure_webhook):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {'id': 12345, 'config': {'url': 'https://api.10ulabs.com/v1/runners'}}
        ]).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = configure_webhook.handle_duplicate_webhook(
            'https://api.10ulabs.com/v1/runners',
            'pat-token',
            '10U-Labs-LLC/10ulabs.com'
        )
    assert result['webhook_id'] == 12345


def test_handle_duplicate_webhook_fails_when_url_not_found(configure_webhook):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {'id': 99999, 'config': {'url': 'https://different-url.com'}}
        ]).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = configure_webhook.handle_duplicate_webhook(
            'https://api.10ulabs.com/v1/runners',
            'pat-token',
            '10U-Labs-LLC/10ulabs.com'
        )
    assert result['success'] is False


def test_send_response_sends_to_cloudformation(configure_webhook):
    event = {
        'ResponseURL': 'https://cloudformation-presigned-url',
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'req-123',
        'LogicalResourceId': 'WebhookConfig'
    }
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = configure_webhook.send_response(event, 'SUCCESS', 'Test', 'physical-id', {})
    assert result is True


def test_send_response_includes_status_in_body(configure_webhook):
    event = {
        'ResponseURL': 'https://cloudformation-presigned-url',
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'req-123',
        'LogicalResourceId': 'WebhookConfig'
    }
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        configure_webhook.send_response(event, 'FAILED', 'Error occurred', 'physical-id', {})
        call_args = mock_urlopen.call_args
        sent_data = json.loads(call_args[0][0].data.decode())
    assert sent_data['Status'] == 'FAILED'


def test_send_response_handles_network_error(configure_webhook):
    import urllib.error
    event = {
        'ResponseURL': 'https://cloudformation-presigned-url',
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'req-123',
        'LogicalResourceId': 'WebhookConfig'
    }
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.URLError('Network error')
        result = configure_webhook.send_response(event, 'SUCCESS', 'Test', 'physical-id', {})
    assert result is False


def test_handle_delete_request_with_no_webhook_id_returns_success(configure_webhook):
    event = {
        'ResourceProperties': {},
        'ResponseURL': 'https://cloudformation-presigned-url',
        'StackId': 'stack-id',
        'RequestId': 'req-id',
        'LogicalResourceId': 'resource-id'
    }
    result = configure_webhook.handle_delete_request(event, '10U-Labs-LLC/10ulabs.com')
    assert result['cf_status'] == 'SUCCESS'


def test_handle_delete_request_with_webhook_id_deletes_webhook(configure_webhook, mock_ssm):
    event = {
        'ResourceProperties': {'WebhookId': '12345'},
        'ResponseURL': 'https://cloudformation-presigned-url',
        'StackId': 'stack-id',
        'RequestId': 'req-id',
        'LogicalResourceId': 'resource-id'
    }
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = configure_webhook.handle_delete_request(event, '10U-Labs-LLC/10ulabs.com')
    assert result['cf_status'] == 'SUCCESS'


def test_handle_delete_request_without_pat_returns_failed(configure_webhook, mock_ssm):
    from botocore.exceptions import ClientError
    event = {
        'ResourceProperties': {'WebhookId': '12345'},
        'ResponseURL': 'https://cloudformation-presigned-url',
        'StackId': 'stack-id',
        'RequestId': 'req-id',
        'LogicalResourceId': 'resource-id'
    }
    mock_ssm.get_parameter.side_effect = ClientError(
        {'Error': {'Code': 'ParameterNotFound'}},
        'GetParameter'
    )
    result = configure_webhook.handle_delete_request(event, '10U-Labs-LLC/10ulabs.com')
    assert result['cf_status'] == 'FAILED'


def test_handle_create_update_request_creates_webhook(configure_webhook, mock_ssm):
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'id': 12345}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = configure_webhook.handle_create_update_request(
            'https://api.10ulabs.com/v1/runners',
            '10U-Labs-LLC/10ulabs.com'
        )
    assert result['cf_status'] == 'SUCCESS'


def test_handle_create_update_request_returns_webhook_data(configure_webhook, mock_ssm):
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'id': 12345}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = configure_webhook.handle_create_update_request(
            'https://api.10ulabs.com/v1/runners',
            '10U-Labs-LLC/10ulabs.com'
        )
    assert result['cf_data']['WebhookId'] == '12345'


def test_handle_create_update_request_without_secrets_returns_failed(configure_webhook):
    from botocore.exceptions import ClientError
    configure_webhook._clients = {'ssm': None}
    with patch('boto3.client') as mock_boto:
        mock_ssm = MagicMock()
        mock_boto.return_value = mock_ssm
        param_not_found = type('ParameterNotFound', (ClientError,), {})
        mock_ssm.exceptions.ParameterNotFound = param_not_found
        error = ClientError(
            {'Error': {'Code': 'ParameterNotFound'}},
            'GetParameter'
        )
        mock_ssm.get_parameter.side_effect = error
        result = configure_webhook.handle_create_update_request(
            'https://api.10ulabs.com/v1/runners',
            '10U-Labs-LLC/10ulabs.com'
        )
    assert result['cf_status'] == 'FAILED'


def test_handler_checks_circuit_breaker_health(circuit_breaker_remediation, env_with_webhook_function_name, lambda_context):
    from unittest.mock import MagicMock, patch
    event = {}
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


def test_handler_returns_circuit_breaker_state(circuit_breaker_remediation, env_with_webhook_function_name, lambda_context):
    from unittest.mock import MagicMock, patch
    event = {}
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


def test_handler_monitors_open_circuit_breaker(circuit_breaker_remediation, env_with_webhook_function_name, lambda_context):
    from unittest.mock import MagicMock, patch
    event = {}
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


def test_handler_does_nothing_for_closed_circuit(circuit_breaker_remediation, env_with_webhook_function_name, lambda_context):
    from unittest.mock import MagicMock, patch
    event = {}
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
    from unittest.mock import patch
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
        result = circuit_breaker_remediation.check_circuit_breaker_health('test-function')
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
    from botocore.exceptions import ClientError
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
    from botocore.exceptions import ClientError
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
    from unittest.mock import patch
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
    from unittest.mock import patch
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
    from unittest.mock import patch
    event = {}
    with patch.dict('os.environ', {
        'WEBHOOK_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/webhook-dlq'
    }):
        response = dlq_reprocessor.handler(event, lambda_context)
        body = parse_response_body(response)
    assert 'note' in body['webhook_dlq']


def test_handler_skips_job_dlq_when_not_configured(dlq_reprocessor, lambda_context):
    from unittest.mock import patch
    event = {}
    with patch.dict('os.environ', {}, clear=True):
        response = dlq_reprocessor.handler(event, lambda_context)
        body = parse_response_body(response)
    assert 'job_dlq' not in body


def test_handler_skips_webhook_dlq_when_not_configured(dlq_reprocessor, lambda_context):
    from unittest.mock import patch
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
    from botocore.exceptions import ClientError
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
    from botocore.exceptions import ClientError
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
    from botocore.exceptions import ClientError
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

def test_stack_creates_github_credentials_ssm_parameter(cdk_template):
    parameters = cdk_template.find_resources("AWS::SSM::Parameter")
    github_creds_param = None
    for key, param in parameters.items():
        if param['Properties']['Name'] == '/github-runner/credentials':
            github_creds_param = param
            break
    assert github_creds_param is not None


def test_github_credentials_parameter_has_placeholder_value(cdk_template):
    parameters = cdk_template.find_resources("AWS::SSM::Parameter")
    github_creds_param = None
    for key, param in parameters.items():
        if param['Properties']['Name'] == '/github-runner/credentials':
            github_creds_param = param
            break
    assert github_creds_param['Properties']['Value'] == 'PLACEHOLDER_UPDATE_WITH_GITHUB_TOKEN'


def test_stack_creates_ami_latest_ssm_parameter(cdk_template):
    parameters = cdk_template.find_resources("AWS::SSM::Parameter")
    ami_param = None
    for key, param in parameters.items():
        if param['Properties']['Name'] == '/github-runner/ami/latest':
            ami_param = param
            break
    assert ami_param is not None


def test_ami_parameter_has_placeholder_value(cdk_template):
    parameters = cdk_template.find_resources("AWS::SSM::Parameter")
    ami_param = None
    for key, param in parameters.items():
        if param['Properties']['Name'] == '/github-runner/ami/latest':
            ami_param = param
            break
    assert ami_param['Properties']['Value'] == 'PLACEHOLDER_UPDATE_AFTER_AMI_BUILD'


def test_v1_handler_has_ssm_policy(cdk_template):
    policies = cdk_template.find_resources("AWS::IAM::Policy")
    v1_handler_policy = None
    for key, policy in policies.items():
        if 'V1ApiHandlerServiceRoleDefaultPolicy' in key:
            v1_handler_policy = policy
            break
    assert v1_handler_policy is not None


def test_v1_handler_policy_has_ssm_get_parameter_statement(cdk_template):
    policies = cdk_template.find_resources("AWS::IAM::Policy")
    v1_handler_policy = None
    for key, policy in policies.items():
        if 'V1ApiHandlerServiceRoleDefaultPolicy' in key:
            v1_handler_policy = policy
            break
    statements = v1_handler_policy['Properties']['PolicyDocument']['Statement']
    ssm_statement = None
    for statement in statements:
        if 'ssm:GetParameter' in statement.get('Action', []):
            ssm_statement = statement
            break
    assert ssm_statement is not None


def test_v1_handler_ssm_policy_uses_wildcard_for_github_runner(cdk_template):
    policies = cdk_template.find_resources("AWS::IAM::Policy")
    v1_handler_policy = None
    for key, policy in policies.items():
        if 'V1ApiHandlerServiceRoleDefaultPolicy' in key:
            v1_handler_policy = policy
            break
    statements = v1_handler_policy['Properties']['PolicyDocument']['Statement']
    ssm_statement = None
    for statement in statements:
        if 'ssm:GetParameter' in statement.get('Action', []):
            ssm_statement = statement
            break
    resources = ssm_statement['Resource']
    if isinstance(resources, str):
        resources = [resources]
    assert any('parameter/github-runner/*' in str(resource) for resource in resources)
