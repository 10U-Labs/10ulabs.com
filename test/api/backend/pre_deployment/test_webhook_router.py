import base64
import json
import os
import time
import urllib.error
import urllib.parse
from unittest.mock import patch, MagicMock
from test.api.backend.pre_deployment.conftest import parse_response_body, assert_response_status, create_multi_client_mock, assert_no_hardcoded_env_defaults, get_lambda_path

import pytest
from botocore.exceptions import ClientError


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


def test_webhook_router_fixture_sets_api_key_parameter_name(webhook_router):
    assert hasattr(webhook_router, 'lambda_handler') and os.environ['API_KEY_PARAMETER_NAME']



def test_lambda_handler_with_invalid_json_returns_400(webhook_router, lambda_context):
    event = {'path': '/v1/runners', 'httpMethod': 'POST', 'body': 'invalid json', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)



def test_lambda_handler_workflow_job_queued_action_returns_200(webhook_router, workflow_job_event_factory, mock_sqs, lambda_context, config):
    mock_sqs.send_message.return_value = {'MessageId': 'test-message-id'}
    mock_sqs.get_queue_attributes.return_value = {'Attributes': {'ApproximateNumberOfMessages': '5'}}
    event = workflow_job_event_factory(action='queued', labels=[config['runner_label_ec2_spot']])
    with patch.object(webhook_router, 'verify_signature', return_value=True):
        with patch.dict('os.environ', {'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'}):
            response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)



def test_lambda_handler_workflow_job_non_queued_action_returns_200(webhook_router, workflow_job_event_factory, lambda_context, config):
    event = workflow_job_event_factory(action='completed', labels=[config['runner_label_ec2_spot']])
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
    mock_boto_client.side_effect = create_multi_client_mock(mock_ec2, mock_ssm)

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b'{"success": true}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    event = sqs_event_factory(records=[{
        'messageId': 'test-message-id',
        'eventSource': 'aws:sqs',
        'body': json.dumps({'job_id': 123, 'job_labels': [os.environ['RUNNER_LABEL_EC2_SPOT']], 'github_repo': 'test-org/test-repo'}),
        'attributes': {},
        'messageAttributes': {}
    }])
    response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)



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



def test_concurrent_idempotency_checks_with_same_id_returns_duplicate(webhook_router):
    with patch('boto3.client') as mock_boto:
        mock_dynamodb = MagicMock()
        mock_boto.return_value = mock_dynamodb
        mock_dynamodb.put_item.return_value = {}
        error = ClientError({'Error': {'Code': 'ConditionalCheckFailedException'}}, 'PutItem')
        mock_dynamodb.put_item.side_effect = [{}, error]
        with patch.dict('os.environ', {'IDEMPOTENCY_TABLE_NAME': 'test-table'}):
            webhook_router.check_and_record_idempotency('same-id')
            second_result = webhook_router.check_and_record_idempotency('same-id')
    assert second_result is True



def test_concurrent_idempotency_checks_with_different_ids_both_succeed(webhook_router):
    with patch('boto3.client') as mock_boto:
        mock_dynamodb = MagicMock()
        mock_boto.return_value = mock_dynamodb
        mock_dynamodb.put_item.return_value = {}
        with patch.dict('os.environ', {'IDEMPOTENCY_TABLE_NAME': 'test-table'}):
            first_result = webhook_router.check_and_record_idempotency('id-1')
            webhook_router.check_and_record_idempotency('id-2')
    assert first_result is False



def test_idempotency_check_handles_dynamodb_error_gracefully(webhook_router):
    with patch('boto3.client') as mock_boto:
        mock_dynamodb = MagicMock()
        mock_boto.return_value = mock_dynamodb
        error = ClientError({'Error': {'Code': 'ServiceUnavailable'}}, 'PutItem')
        mock_dynamodb.put_item.side_effect = error
        with patch.dict('os.environ', {'IDEMPOTENCY_TABLE_NAME': 'test-table'}):
            result = webhook_router.check_and_record_idempotency('test-id')
    assert result is False



def test_idempotency_check_without_table_name_returns_false(webhook_router):
    with patch.dict('os.environ', {}, clear=True):
        result = webhook_router.check_and_record_idempotency('test-id')
    assert result is False



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



def test_route_runner_request_with_ec2_label_calls_ec2_endpoint(webhook_router, config):
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    with patch('boto3.client'), patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'success': True}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = webhook_router.route_runner_request(123, [config['runner_label_ec2_spot']], 'test/repo')
    assert result['success'] is True



def test_route_runner_request_with_fargate_label_calls_docker_endpoint(webhook_router, config):
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    with patch('boto3.client'), patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'success': True}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = webhook_router.route_runner_request(123, [config['runner_label_fargate_spot']], 'test/repo')
    assert result['success'] is True



def test_route_runner_request_with_no_matching_labels_returns_error(webhook_router):
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    with patch('boto3.client'):
        result = webhook_router.route_runner_request(123, ['other-label'], 'test/repo')
    assert result['success'] is False



def test_route_runner_request_rejected_when_circuit_breaker_open(webhook_router, config):
    webhook_router.circuit_breaker_state['state'] = 'open'
    webhook_router.circuit_breaker_state['last_failure_time'] = time.time()
    with patch('boto3.client'):
        result = webhook_router.route_runner_request(123, [config['runner_label_ec2_spot']], 'test/repo')
    assert result['success'] is False


def test_route_runner_request_503_does_not_trigger_circuit_breaker_failure(webhook_router, config):
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    with patch('boto3.client'), patch('urllib.request.urlopen') as mock_urlopen, patch('time.sleep'):
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 503, 'Service Unavailable', {}, None)
        with patch.object(webhook_router, 'record_circuit_breaker_failure') as mock_record:
            webhook_router.route_runner_request(123, [config['runner_label_ec2_spot']], 'test/repo')
            mock_record.assert_not_called()


def test_route_runner_request_500_triggers_circuit_breaker_failure(webhook_router, config):
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    with patch('boto3.client'), patch('urllib.request.urlopen') as mock_urlopen, patch('time.sleep'):
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 500, 'Internal Server Error', {}, None)
        with patch.object(webhook_router, 'record_circuit_breaker_failure') as mock_record:
            webhook_router.route_runner_request(123, [config['runner_label_ec2_spot']], 'test/repo')
            mock_record.assert_called_once()


def test_handle_workflow_job_enqueues_ec2_job(webhook_router, mock_sqs, config):
    event_data = {
        'action': 'queued',
        'workflow_job': {
            'id': 123,
            'name': 'test',
            'labels': [config['runner_label_ec2_spot']],
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



def test_handle_workflow_job_enqueues_fargate_job(webhook_router, mock_sqs, config):
    event_data = {
        'action': 'queued',
        'workflow_job': {
            'id': 456,
            'name': 'test',
            'labels': [config['runner_label_fargate_spot']],
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



def test_handle_sqs_message_processes_valid_message(webhook_router, config):
    message = {
        'body': json.dumps({
            'job_id': 123,
            'job_labels': [config['runner_label_ec2_spot']],
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
        success, _data, _error, _status = webhook_router.make_http_request_with_retry('http://test.com', {})
    assert success is True


def test_make_http_request_with_retry_retries_on_server_error_returns_false(webhook_router):
    with patch('urllib.request.urlopen') as mock_urlopen, patch('time.sleep'):
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 500, 'Server Error', {}, None)
        success, _data, _error, _status = webhook_router.make_http_request_with_retry('http://test.com', {}, max_retries=1)
    assert success is False


def test_make_http_request_with_retry_retries_on_server_error_returns_status_code(webhook_router):
    with patch('urllib.request.urlopen') as mock_urlopen, patch('time.sleep'):
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 500, 'Server Error', {}, None)
        _success, _data, _error, status = webhook_router.make_http_request_with_retry('http://test.com', {}, max_retries=1)
    assert status == 500


def test_make_http_request_with_retry_fails_immediately_on_client_error_returns_false(webhook_router):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 400, 'Bad Request', {}, None)
        success, _data, _error, _status = webhook_router.make_http_request_with_retry('http://test.com', {})
    assert success is False


def test_make_http_request_with_retry_fails_immediately_on_client_error_returns_status_code(webhook_router):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 400, 'Bad Request', {}, None)
        _success, _data, _error, status = webhook_router.make_http_request_with_retry('http://test.com', {})
    assert status == 400


def test_make_http_request_with_retry_returns_503_returns_false(webhook_router):
    with patch('urllib.request.urlopen') as mock_urlopen, patch('time.sleep'):
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 503, 'Service Unavailable', {}, None)
        success, _data, _error, _status = webhook_router.make_http_request_with_retry('http://test.com', {}, max_retries=1)
    assert success is False


def test_make_http_request_with_retry_returns_503_status_code(webhook_router):
    with patch('urllib.request.urlopen') as mock_urlopen, patch('time.sleep'):
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 503, 'Service Unavailable', {}, None)
        _success, _data, _error, status = webhook_router.make_http_request_with_retry('http://test.com', {}, max_retries=1)
    assert status == 503


def test_publish_metric_sends_to_cloudwatch(webhook_router, mock_cloudwatch):
    webhook_router.publish_metric('TestMetric', 1.0, 'Count')
    assert mock_cloudwatch.put_metric_data.call_count == 1


def test_publish_metric_skips_when_test_mode_enabled(webhook_router, mock_cloudwatch):
    webhook_router.set_test_mode(True)
    webhook_router.publish_metric('TestMetric', 1.0, 'Count')
    webhook_router.set_test_mode(False)
    assert mock_cloudwatch.put_metric_data.call_count == 0


def test_set_test_mode_enables_test_mode(webhook_router):
    webhook_router.set_test_mode(True)
    assert webhook_router.test_mode_enabled['value'] is True
    webhook_router.set_test_mode(False)


def test_set_test_mode_disables_test_mode(webhook_router):
    webhook_router.set_test_mode(True)
    webhook_router.set_test_mode(False)
    assert webhook_router.test_mode_enabled['value'] is False


def test_handle_api_gateway_event_enables_test_mode_with_header(webhook_router):
    event = {'path': '/v1/runners/health', 'httpMethod': 'GET', 'headers': {'x-test-mode': 'true'}}
    webhook_router.handle_api_gateway_event(event, time.time())
    result = webhook_router.test_mode_enabled['value']
    webhook_router.set_test_mode(False)
    assert result is True


def test_handle_api_gateway_event_disables_test_mode_without_header(webhook_router):
    webhook_router.set_test_mode(True)
    event = {'path': '/v1/runners/health', 'httpMethod': 'GET', 'headers': {}}
    webhook_router.handle_api_gateway_event(event, time.time())
    assert webhook_router.test_mode_enabled['value'] is False


def test_handle_api_gateway_event_detects_uppercase_test_mode_header(webhook_router):
    event = {'path': '/v1/runners/health', 'httpMethod': 'GET', 'headers': {'X-Test-Mode': 'true'}}
    webhook_router.handle_api_gateway_event(event, time.time())
    result = webhook_router.test_mode_enabled['value']
    webhook_router.set_test_mode(False)
    assert result is True


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



def test_handle_api_gateway_event_with_workflow_job_processes_correctly(webhook_router, config):
    event = {
        'path': '/v1/runners',
        'body': json.dumps({
            'action': 'queued',
            'workflow_job': {
                'id': 123,
                'name': 'test',
                'labels': [config['runner_label_ec2_spot']],
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




def test_no_hardcoded_defaults_in_webhook_router():
    assert_no_hardcoded_env_defaults(get_lambda_path("webhook_router.py"))



@patch('boto3.client')
def test_get_ssm_client_initialization_webhook_router(_mock_boto_client, webhook_router):
    webhook_router.clients['ssm'] = None
    client = webhook_router.get_ssm_client()
    assert client is not None



@patch('boto3.client')
def test_get_ssm_client_caching_webhook_router(mock_boto_client, webhook_router):
    mock_ssm = MagicMock()
    mock_boto_client.return_value = mock_ssm
    webhook_router.clients['ssm'] = None
    client1 = webhook_router.get_ssm_client()
    client2 = webhook_router.get_ssm_client()
    assert client1 is client2



@patch('boto3.client')
def test_get_dynamodb_client_initialization_webhook_router(_mock_boto_client, webhook_router):
    webhook_router.clients['dynamodb'] = None
    client = webhook_router.get_dynamodb_client()
    assert client is not None



@patch('boto3.client')
def test_get_cloudwatch_client_initialization_webhook_router(_mock_boto_client, webhook_router):
    webhook_router.clients['cloudwatch'] = None
    client = webhook_router.get_cloudwatch_client()
    assert client is not None



def test_get_header_case_insensitive_matching(webhook_router):
    headers = {'Content-Type': 'application/json', 'X-Custom-Header': 'value'}
    result = webhook_router.get_header_case_insensitive(headers, 'content-type')
    assert result == 'application/json'



def test_get_header_case_insensitive_case_mismatch(webhook_router):
    headers = {'x-github-event': 'workflow_job'}
    result = webhook_router.get_header_case_insensitive(headers, 'X-GitHub-Event')
    assert result == 'workflow_job'



def test_get_header_case_insensitive_missing(webhook_router):
    headers = {'Content-Type': 'application/json'}
    result = webhook_router.get_header_case_insensitive(headers, 'missing-header')
    assert result is None



def test_get_api_key_cached_value(webhook_router):
    webhook_router.api_key_cache['value'] = 'cached-key'
    result = webhook_router.get_api_key()
    assert result == 'cached-key'



@patch('boto3.client')
def test_get_api_key_missing_env_var_raises_runtime_error(_mock_boto_client, webhook_router):
    webhook_router.api_key_cache['value'] = None
    raised_error = None
    with patch.dict('os.environ', {}, clear=True):
        try:
            webhook_router.get_api_key()
        except RuntimeError as e:
            raised_error = e
    assert raised_error is not None


@patch('boto3.client')
def test_get_api_key_missing_env_var_error_mentions_parameter_name(_mock_boto_client, webhook_router):
    webhook_router.api_key_cache['value'] = None
    raised_error = None
    with patch.dict('os.environ', {}, clear=True):
        try:
            webhook_router.get_api_key()
        except RuntimeError as e:
            raised_error = e
    assert 'API_KEY_PARAMETER_NAME' in str(raised_error)



def test_route_runner_request_ssm_failure(webhook_router, config):
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    with patch('boto3.client'):
        with patch.object(webhook_router, 'get_api_key', side_effect=RuntimeError('SSM error')):
            with patch.dict('os.environ', {'API_BASE_URL': 'https://api.test.com'}):
                result = webhook_router.route_runner_request(123, [config['runner_label_ec2_spot']], 'test/repo')
                assert result['success'] is False



@patch('boto3.client')
def test_enqueue_job_sqs_send_failure(mock_boto_client, webhook_router):
    mock_sqs = MagicMock()
    mock_sqs.send_message.side_effect = ClientError({'Error': {'Code': 'TestError'}}, 'SendMessage')
    mock_boto_client.return_value = mock_sqs
    with patch.dict('os.environ', {'JOB_QUEUE_URL': 'https://sqs.test.com/queue'}):
        result = webhook_router.enqueue_job({'job_id': 123})
        assert result['success'] is False



def test_check_and_record_idempotency_missing_table(webhook_router):
    with patch.dict('os.environ', {}, clear=True):
        result = webhook_router.check_and_record_idempotency('test-id')
        assert result is False



@patch('boto3.client')
def test_check_and_record_idempotency_dynamodb_error(mock_boto_client, webhook_router):
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.side_effect = ClientError({'Error': {'Code': 'ServiceUnavailable'}}, 'PutItem')
    mock_boto_client.return_value = mock_dynamodb
    with patch.dict('os.environ', {'IDEMPOTENCY_TABLE_NAME': 'test-table'}):
        result = webhook_router.check_and_record_idempotency('test-id')
        assert result is False



def test_handle_api_gateway_event_missing_signature(webhook_router):
    event = {
        'path': '/v1/runners',
        'body': json.dumps({'action': 'queued'}),
        'headers': {}
    }
    with patch('boto3.client'):
        result = webhook_router.handle_api_gateway_event(event, time.time())
        assert result['statusCode'] == 200



@patch('boto3.client')
def test_publish_metric_cloudwatch_failure(mock_boto_client, webhook_router):
    mock_cw = MagicMock()
    mock_cw.put_metric_data.side_effect = ClientError({'Error': {'Code': 'TestError'}}, 'PutMetricData')
    mock_boto_client.return_value = mock_cw
    webhook_router.publish_metric('TestMetric', 1.0)
    assert True





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



def test_lambda_handler_options_request_returns_200(webhook_router, lambda_context):
    event = {'path': '/v1/runners', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)



def test_lambda_handler_options_request_returns_allow_origin_header(webhook_router, lambda_context):
    event = {'path': '/v1/runners', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    assert 'Access-Control-Allow-Origin' in headers


def test_lambda_handler_options_request_returns_allow_methods_header(webhook_router, lambda_context):
    event = {'path': '/v1/runners', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    assert 'Access-Control-Allow-Methods' in headers


def test_lambda_handler_options_request_returns_allow_headers_header(webhook_router, lambda_context):
    event = {'path': '/v1/runners', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    assert 'Access-Control-Allow-Headers' in headers



def test_lambda_handler_options_request_allows_wildcard_origin(webhook_router, lambda_context):
    event = {'path': '/v1/runners', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    assert headers['Access-Control-Allow-Origin'] == '*'



def test_lambda_handler_options_request_allows_get_method(webhook_router, lambda_context):
    event = {'path': '/v1/runners', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    allowed_methods = headers['Access-Control-Allow-Methods']
    assert 'GET' in allowed_methods


def test_lambda_handler_options_request_allows_post_method(webhook_router, lambda_context):
    event = {'path': '/v1/runners', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    allowed_methods = headers['Access-Control-Allow-Methods']
    assert 'POST' in allowed_methods


def test_lambda_handler_options_request_allows_options_method(webhook_router, lambda_context):
    event = {'path': '/v1/runners', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    allowed_methods = headers['Access-Control-Allow-Methods']
    assert 'OPTIONS' in allowed_methods


def test_should_record_circuit_breaker_failure_returns_false_for_503(webhook_router):
    assert webhook_router.should_record_circuit_breaker_failure(503) is False


def test_should_record_circuit_breaker_failure_returns_true_for_500(webhook_router):
    assert webhook_router.should_record_circuit_breaker_failure(500) is True


def test_should_record_circuit_breaker_failure_returns_true_for_502(webhook_router):
    assert webhook_router.should_record_circuit_breaker_failure(502) is True


def test_should_record_circuit_breaker_failure_returns_true_for_504(webhook_router):
    assert webhook_router.should_record_circuit_breaker_failure(504) is True


def test_should_record_circuit_breaker_failure_returns_false_for_400(webhook_router):
    assert webhook_router.should_record_circuit_breaker_failure(400) is False


def test_should_record_circuit_breaker_failure_returns_false_for_200(webhook_router):
    assert webhook_router.should_record_circuit_breaker_failure(200) is False


def test_should_record_circuit_breaker_failure_returns_true_for_none(webhook_router):
    assert webhook_router.should_record_circuit_breaker_failure(None) is True
