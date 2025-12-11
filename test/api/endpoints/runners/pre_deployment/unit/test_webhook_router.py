"""Unit tests for test webhook router."""
import base64
import json
import os
import time
import urllib.error
import urllib.parse
from unittest.mock import patch, MagicMock

import pytest
from botocore.exceptions import ClientError

from .conftest import (
    parse_response_body,
    assert_response_status,
    create_multi_client_mock,
    assert_no_hardcoded_env_defaults,
    get_lambda_path,
)


def test_lambda_handler_health_check_returns_200(webhook_router, lambda_context):
    """Test lambda handler health check returns 200."""
    event = {'path': '/v1/runners/health', 'httpMethod': 'GET'}
    response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)



def test_lambda_handler_health_check_returnscircuit_breaker_state(webhook_router, lambda_context):
    """Test lambda handler health check returnscircuit breaker state."""
    event = {'path': '/v1/runners/health', 'httpMethod': 'GET'}
    response = webhook_router.lambda_handler(event, lambda_context)
    body = parse_response_body(response)
    assert 'circuit_breaker' in body



def test_lambda_handler_health_check_returns_healthy_status(webhook_router, lambda_context):
    """Test lambda handler health check returns healthy status."""
    event = {'path': '/v1/runners/health', 'httpMethod': 'GET'}
    response = webhook_router.lambda_handler(event, lambda_context)
    body = parse_response_body(response)
    assert body['status'] == 'healthy'


def test_webhook_router_fixture_sets_api_key_parameter_name(webhook_router):
    """Test webhook router fixture sets api key parameter name."""
    has_handler = hasattr(webhook_router, 'lambda_handler')
    has_param = os.environ['API_KEY_PARAMETER_NAME']
    assert has_handler and has_param



def test_lambda_handler_with_invalid_json_returns_400(webhook_router, lambda_context):
    """Test lambda handler with invalid json returns 400."""
    event = {'path': '/v1/runners', 'httpMethod': 'POST', 'body': 'invalid json', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)



def test_lambda_handler_workflow_job_queued_action_returns_200(
    webhook_router, workflow_job_event_factory, mock_sqs, lambda_context, config
):
    """Test lambda handler workflow job queued action returns 200."""
    mock_sqs.send_message.return_value = {'MessageId': 'test-message-id'}
    attrs = {'Attributes': {'ApproximateNumberOfMessages': '5'}}
    mock_sqs.get_queue_attributes.return_value = attrs
    event = workflow_job_event_factory(action='queued', labels=config['ec2'])
    queue_url = 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'
    with patch.object(webhook_router, 'verify_signature', return_value=True):
        with patch.dict('os.environ', {'JOB_QUEUE_URL': queue_url}):
            response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)



def test_lambda_handler_workflow_job_non_queued_action_returns_200(
    webhook_router, workflow_job_event_factory, lambda_context, config
):
    """Test lambda handler workflow job non queued action returns 200."""
    event = workflow_job_event_factory(action='completed', labels=config['ec2'])
    with patch.object(webhook_router, 'verify_signature', return_value=True):
        with patch('boto3.client'):
            response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)



def test_lambda_handler_workflow_job_without_matching_labels_returns_200(
    webhook_router, workflow_job_event_factory, lambda_context
):
    """Test lambda handler workflow job without matching labels returns 200."""
    event = workflow_job_event_factory(action='queued', labels=['some-other-label'])
    with patch.object(webhook_router, 'verify_signature', return_value=True):
        with patch('boto3.client'):
            response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)



def test_lambda_handler_ping_event_returns_200(webhook_router, lambda_context):
    """Test lambda handler ping event returns 200."""
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
def test_lambda_handler_sqs_event_processes_successfully(
    mock_boto_client, mock_urlopen, webhook_router, sqs_event_factory, lambda_context, config
):
    """Test lambda handler sqs event processes successfully."""
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

    job_data = {
        'job_id': 123,
        'job_labels': config['ec2'],
        'github_repo': 'test-org/test-repo'
    }
    event = sqs_event_factory(records=[{
        'messageId': 'test-message-id',
        'eventSource': 'aws:sqs',
        'body': json.dumps(job_data),
        'attributes': {},
        'messageAttributes': {}
    }])
    response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)



def test_check_and_record_idempotency_with_new_request_returns_false(webhook_router):
    """Test check and record idempotency with new request returns false."""
    result = webhook_router.check_and_record_idempotency('test-request-id')
    assert result is False



def test_check_and_record_idempotency_with_duplicate_request_returns_true(webhook_router):
    """Test check and record idempotency with duplicate request returns true."""
    with patch('boto3.client') as mock_boto:
        mock_dynamodb = MagicMock()
        mock_boto.return_value = mock_dynamodb
        error = ClientError({'Error': {'Code': 'ConditionalCheckFailedException'}}, 'PutItem')
        mock_dynamodb.put_item.side_effect = error
        with patch.dict('os.environ', {'IDEMPOTENCY_TABLE_NAME': 'test-table'}):
            result = webhook_router.check_and_record_idempotency('duplicate-id')
    assert result is True



def test_concurrent_idempotency_checks_with_same_id_returns_duplicate(webhook_router):
    """Test concurrent idempotency checks with same id returns duplicate."""
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
    """Test concurrent idempotency checks with different ids both succeed."""
    with patch('boto3.client') as mock_boto:
        mock_dynamodb = MagicMock()
        mock_boto.return_value = mock_dynamodb
        mock_dynamodb.put_item.return_value = {}
        with patch.dict('os.environ', {'IDEMPOTENCY_TABLE_NAME': 'test-table'}):
            first_result = webhook_router.check_and_record_idempotency('id-1')
            webhook_router.check_and_record_idempotency('id-2')
    assert first_result is False



def test_idempotency_check_handles_dynamodb_error_gracefully(webhook_router):
    """Test idempotency check handles dynamodb error gracefully."""
    with patch('boto3.client') as mock_boto:
        mock_dynamodb = MagicMock()
        mock_boto.return_value = mock_dynamodb
        error = ClientError({'Error': {'Code': 'ServiceUnavailable'}}, 'PutItem')
        mock_dynamodb.put_item.side_effect = error
        with patch.dict('os.environ', {'IDEMPOTENCY_TABLE_NAME': 'test-table'}):
            result = webhook_router.check_and_record_idempotency('test-id')
    assert result is False



def test_idempotency_check_without_table_name_returns_false(webhook_router):
    """Test idempotency check without table name returns false."""
    with patch.dict('os.environ', {}, clear=True):
        result = webhook_router.check_and_record_idempotency('test-id')
    assert result is False



def test_enqueue_job_succeeds_and_returns_message_id(webhook_router, mock_sqs):
    """Test enqueue job succeeds and returns message id."""
    mock_sqs.send_message.return_value = {'MessageId': 'msg-123'}
    mock_sqs.get_queue_attributes.return_value = {
        'Attributes': {'ApproximateNumberOfMessages': '5'}
    }
    queue_url = 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'
    with patch.dict('os.environ', {'JOB_QUEUE_URL': queue_url}):
        result = webhook_router.enqueue_job({'job_id': 123})
    assert result['success'] is True



def test_enqueue_job_returns_error_when_queue_url_not_set(webhook_router):
    """Test enqueue job returns error when queue url not set."""
    with patch.dict('os.environ', {}, clear=True):
        result = webhook_router.enqueue_job({'job_id': 123})
    assert result['success'] is False



def test_route_runner_request_with_ec2_label_calls_ec2_endpoint(webhook_router, config):
    """Test route runner request with ec2 label calls ec2 endpoint."""
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    with patch('boto3.client'), patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'success': True}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = webhook_router.route_runner_request(123, config['ec2'], 'test/repo')
    assert result['success'] is True



def test_route_runner_request_with_fargate_label_calls_docker_endpoint(webhook_router, config):
    """Test route runner request with fargate label calls docker endpoint."""
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    with patch('boto3.client'), patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'success': True}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = webhook_router.route_runner_request(123, config['fargate'], 'test/repo')
    assert result['success'] is True



def test_route_runner_request_with_no_matching_labels_returns_error(webhook_router):
    """Test route runner request with no matching labels returns error."""
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    with patch('boto3.client'):
        result = webhook_router.route_runner_request(123, ['other-label'], 'test/repo')
    assert result['success'] is False



def test_route_runner_request_rejected_when_circuit_breaker_open(webhook_router, config):
    """Test route runner request rejected when circuit breaker open."""
    webhook_router.circuit_breaker_state['state'] = 'open'
    webhook_router.circuit_breaker_state['last_failure_time'] = time.time()
    with patch('boto3.client'):
        result = webhook_router.route_runner_request(123, config['ec2'], 'test/repo')
    assert result['success'] is False


def test_route_runner_request_503_does_not_trigger_circuit_breaker_failure(webhook_router, config):
    """Test route runner request 503 does not trigger circuit breaker failure."""
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    http_error = urllib.error.HTTPError('url', 503, 'Service Unavailable', {}, None)
    with patch('boto3.client'), \
         patch('urllib.request.urlopen', side_effect=http_error), \
         patch('time.sleep'), \
         patch.object(webhook_router, 'record_circuit_breaker_failure') as mock_record:
        webhook_router.route_runner_request(123, config['ec2'], 'test/repo')
        mock_record.assert_not_called()


def test_route_runner_request_500_triggers_circuit_breaker_failure(webhook_router, config):
    """Test route runner request 500 triggers circuit breaker failure."""
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    http_error = urllib.error.HTTPError('url', 500, 'Internal Server Error', {}, None)
    with patch('boto3.client'), \
         patch('urllib.request.urlopen', side_effect=http_error), \
         patch('time.sleep'), \
         patch.object(webhook_router, 'record_circuit_breaker_failure') as mock_record:
        webhook_router.route_runner_request(123, config['ec2'], 'test/repo')
        mock_record.assert_called_once()


def test_handle_workflow_job_enqueues_ec2_job(webhook_router, mock_sqs, config):
    """Test handle workflow job enqueues ec2 job."""
    event_data = {
        'action': 'queued',
        'workflow_job': {
            'id': 123,
            'name': 'test',
            'labels': config['ec2'],
            'status': 'queued'
        },
        'repository': {'full_name': 'test/repo'}
    }
    mock_sqs.send_message.return_value = {'MessageId': 'msg-123'}
    mock_sqs.get_queue_attributes.return_value = {
        'Attributes': {'ApproximateNumberOfMessages': '0'}
    }
    queue_url = 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'
    with patch.dict('os.environ', {'JOB_QUEUE_URL': queue_url}):
        result = webhook_router.handle_workflow_job(event_data)
    assert result['statusCode'] == 200



def test_handle_workflow_job_enqueues_fargate_job(webhook_router, mock_sqs, config):
    """Test handle workflow job enqueues fargate job."""
    event_data = {
        'action': 'queued',
        'workflow_job': {
            'id': 456,
            'name': 'test',
            'labels': config['fargate'],
            'status': 'queued'
        },
        'repository': {'full_name': 'test/repo'}
    }
    mock_sqs.send_message.return_value = {'MessageId': 'msg-456'}
    mock_sqs.get_queue_attributes.return_value = {
        'Attributes': {'ApproximateNumberOfMessages': '0'}
    }
    queue_url = 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'
    with patch.dict('os.environ', {'JOB_QUEUE_URL': queue_url}):
        result = webhook_router.handle_workflow_job(event_data)
    assert result['statusCode'] == 200



def test_handle_sqs_message_processes_valid_message(webhook_router, config):
    """Test handle sqs message processes valid message."""
    message = {
        'body': json.dumps({
            'job_id': 123,
            'job_labels': config['ec2'],
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
    """Test handle sqs message with invalid json returns error."""
    message = {'body': 'invalid json'}
    result = webhook_router.handle_sqs_message(message)
    assert result['success'] is False



def test_parse_event_body_with_json_string_returns_dict(webhook_router):
    """Test parse event body with json string returns dict."""
    event = {'body': json.dumps({'key': 'value'})}
    _body_str, payload = webhook_router.parse_event_body(event)
    assert payload['key'] == 'value'



def test_parse_event_body_with_base64_encoded_body_decodes_correctly(webhook_router):
    """Test parse event body with base64 encoded body decodes correctly."""
    body = json.dumps({'key': 'value'})
    encoded = base64.b64encode(body.encode()).decode()
    event = {'body': encoded, 'isBase64Encoded': True}
    _body_str, payload = webhook_router.parse_event_body(event)
    assert payload['key'] == 'value'



def test_parse_event_body_with_form_urlencoded_payload_parses_correctly(webhook_router):
    """Test parse event body with form urlencoded payload parses correctly."""
    payload = {'key': 'value'}
    encoded = 'payload=' + urllib.parse.quote(json.dumps(payload))
    event = {'body': encoded}
    _body_str, parsed_payload = webhook_router.parse_event_body(event)
    assert parsed_payload['key'] == 'value'



def test_get_webhook_secret_retrieves_from_ssm(webhook_router, mock_ssm):
    """Test get webhook secret retrieves from ssm."""
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': 'test-secret'}
    }
    secret = webhook_router.get_webhook_secret()
    assert secret == 'test-secret'



def test_getwebhook_secret_caches_value(webhook_router, mock_ssm):
    """Test getwebhook secret caches value."""
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': 'test-secret'}
    }
    webhook_router.get_webhook_secret()
    webhook_router.get_webhook_secret()
    assert mock_ssm.get_parameter.call_count == 1



def test_get_webhook_secret_force_refresh_clears_cache(webhook_router, mock_ssm):
    """Test get webhook secret force refresh clears cache."""
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': 'test-secret'}
    }
    webhook_router.webhook_secret_cache['value'] = 'old-secret'
    secret = webhook_router.get_webhook_secret(force_refresh=True)
    assert secret == 'test-secret'



def test_make_http_request_with_retry_succeeds_on_first_attempt(webhook_router):
    """Test make http request with retry succeeds on first attempt."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'result': 'success'}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = webhook_router.make_http_request_with_retry('http://test.com', {})
        success, _data, _error, _status = result
    assert success is True


def test_make_http_request_with_retry_retries_on_server_error_returns_false(webhook_router):
    """Test make http request with retry retries on server error returns false."""
    with patch('urllib.request.urlopen') as mock_urlopen, patch('time.sleep'):
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 500, 'Server Error', {}, None)
        result = webhook_router.make_http_request_with_retry(
            'http://test.com', {}, max_retries=1
        )
        success, _data, _error, _status = result
    assert success is False


def test_make_http_request_with_retry_retries_on_server_error_returns_status_code(webhook_router):
    """Test make http request with retry retries on server error returns status code."""
    with patch('urllib.request.urlopen') as mock_urlopen, patch('time.sleep'):
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 500, 'Server Error', {}, None)
        result = webhook_router.make_http_request_with_retry(
            'http://test.com', {}, max_retries=1
        )
        _success, _data, _error, status = result
    assert status == 500


def test_make_http_request_with_retry_fails_immediately_on_client_error_returns_false(
    webhook_router
):
    """Test make http request with retry fails immediately on client error returns false."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 400, 'Bad Request', {}, None)
        result = webhook_router.make_http_request_with_retry('http://test.com', {})
        success, _data, _error, _status = result
    assert success is False


def test_make_http_request_with_retry_fails_immediately_on_client_error_returns_status_code(
    webhook_router
):
    """Test make http request with retry fails immediately on client error returns status code."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 400, 'Bad Request', {}, None)
        result = webhook_router.make_http_request_with_retry('http://test.com', {})
        _success, _data, _error, status = result
    assert status == 400


def test_make_http_request_with_retry_returns_503_returns_false(webhook_router):
    """Test make http request with retry returns 503 returns false."""
    with patch('urllib.request.urlopen') as mock_urlopen, patch('time.sleep'):
        http_error = urllib.error.HTTPError('url', 503, 'Service Unavailable', {}, None)
        mock_urlopen.side_effect = http_error
        result = webhook_router.make_http_request_with_retry(
            'http://test.com', {}, max_retries=1
        )
        success, _data, _error, _status = result
    assert success is False


def test_make_http_request_with_retry_returns_503_status_code(webhook_router):
    """Test make http request with retry returns 503 status code."""
    with patch('urllib.request.urlopen') as mock_urlopen, patch('time.sleep'):
        http_error = urllib.error.HTTPError('url', 503, 'Service Unavailable', {}, None)
        mock_urlopen.side_effect = http_error
        result = webhook_router.make_http_request_with_retry(
            'http://test.com', {}, max_retries=1
        )
        _success, _data, _error, status = result
    assert status == 503


def test_publish_metric_sends_to_cloudwatch(webhook_router, mock_cloudwatch):
    """Test publish metric sends to cloudwatch."""
    webhook_router.publish_metric('TestMetric', 1.0, 'Count')
    assert mock_cloudwatch.put_metric_data.call_count == 1


def test_publish_metric_skips_when_test_mode_enabled(webhook_router, mock_cloudwatch):
    """Test publish metric skips when mode enabled."""
    webhook_router.set_test_mode(True)
    webhook_router.publish_metric('TestMetric', 1.0, 'Count')
    webhook_router.set_test_mode(False)
    assert mock_cloudwatch.put_metric_data.call_count == 0


def test_set_test_mode_enables_test_mode(webhook_router):
    """Test set mode enables mode."""
    webhook_router.set_test_mode(True)
    assert webhook_router.test_mode_enabled['value'] is True
    webhook_router.set_test_mode(False)


def test_set_test_mode_disables_test_mode(webhook_router):
    """Test set mode disables mode."""
    webhook_router.set_test_mode(True)
    webhook_router.set_test_mode(False)
    assert webhook_router.test_mode_enabled['value'] is False


def test_handle_api_gateway_event_enables_test_mode_with_header(webhook_router):
    """Test handle api gateway event enables mode with header."""
    event = {'path': '/v1/runners/health', 'httpMethod': 'GET', 'headers': {'x-test-mode': 'true'}}
    webhook_router.handle_api_gateway_event(event, time.time())
    result = webhook_router.test_mode_enabled['value']
    webhook_router.set_test_mode(False)
    assert result is True


def test_handle_api_gateway_event_disables_test_mode_without_header(webhook_router):
    """Test handle api gateway event disables mode without header."""
    webhook_router.set_test_mode(True)
    event = {'path': '/v1/runners/health', 'httpMethod': 'GET', 'headers': {}}
    webhook_router.handle_api_gateway_event(event, time.time())
    assert webhook_router.test_mode_enabled['value'] is False


def test_handle_api_gateway_event_detects_uppercase_test_mode_header(webhook_router):
    """Test handle api gateway event detects uppercase mode header."""
    event = {'path': '/v1/runners/health', 'httpMethod': 'GET', 'headers': {'X-Test-Mode': 'true'}}
    webhook_router.handle_api_gateway_event(event, time.time())
    result = webhook_router.test_mode_enabled['value']
    webhook_router.set_test_mode(False)
    assert result is True


def test_verify_webhook_signature_with_valid_signature_returns_empty_dict(webhook_router, mock_ssm):
    """Test verify webhook signature with valid signature returns empty dict."""
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
    """Test verify webhook signature with invalid signature returns 401."""
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': 'test-secret'}
    }
    webhook_router.webhook_secret_cache['value'] = None
    result = webhook_router.verify_webhook_signature('payload', 'sha256=invalid')
    assert result['statusCode'] == 401



def test_handle_api_gateway_event_with_workflow_job_processes_correctly(webhook_router, config):
    """Test handle api gateway event with workflow job processes correctly."""
    event = {
        'path': '/v1/runners',
        'body': json.dumps({
            'action': 'queued',
            'workflow_job': {
                'id': 123,
                'name': 'test',
                'labels': config['ec2'],
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
        queue_url = 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'
        with patch.dict('os.environ', {'JOB_QUEUE_URL': queue_url}):
            result = webhook_router.handle_api_gateway_event(event, time.time())
    assert result['statusCode'] == 200



def test_lambda_handler_sqs_event_with_failed_message_raises_error(webhook_router, lambda_context):
    """Test lambda handler sqs event with failed message raises error."""
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
    """Test no hardcoded defaults in webhook router."""
    assert_no_hardcoded_env_defaults(get_lambda_path("webhook_router.py"))



@patch('boto3.client')
def test_get_ssm_client_initialization_webhook_router(_mock_boto_client, webhook_router):
    """Test get ssm client initialization webhook router."""
    webhook_router.clients['ssm'] = None
    client = webhook_router.get_ssm_client()
    assert client is not None



@patch('boto3.client')
def test_get_ssm_client_caching_webhook_router(mock_boto_client, webhook_router):
    """Test get ssm client caching webhook router."""
    mock_ssm = MagicMock()
    mock_boto_client.return_value = mock_ssm
    webhook_router.clients['ssm'] = None
    client1 = webhook_router.get_ssm_client()
    client2 = webhook_router.get_ssm_client()
    assert client1 is client2



@patch('boto3.client')
def test_get_dynamodb_client_initialization_webhook_router(_mock_boto_client, webhook_router):
    """Test get dynamodb client initialization webhook router."""
    webhook_router.clients['dynamodb'] = None
    client = webhook_router.get_dynamodb_client()
    assert client is not None



@patch('boto3.client')
def test_get_cloudwatch_client_initialization_webhook_router(_mock_boto_client, webhook_router):
    """Test get cloudwatch client initialization webhook router."""
    webhook_router.clients['cloudwatch'] = None
    client = webhook_router.get_cloudwatch_client()
    assert client is not None



def test_get_header_case_insensitive_matching(webhook_router):
    """Test get header case insensitive matching."""
    headers = {'Content-Type': 'application/json', 'X-Custom-Header': 'value'}
    result = webhook_router.get_header_case_insensitive(headers, 'content-type')
    assert result == 'application/json'



def test_get_header_case_insensitive_case_mismatch(webhook_router):
    """Test get header case insensitive case mismatch."""
    headers = {'x-github-event': 'workflow_job'}
    result = webhook_router.get_header_case_insensitive(headers, 'X-GitHub-Event')
    assert result == 'workflow_job'



def test_get_header_case_insensitive_missing(webhook_router):
    """Test get header case insensitive missing."""
    headers = {'Content-Type': 'application/json'}
    result = webhook_router.get_header_case_insensitive(headers, 'missing-header')
    assert result is None



def test_get_api_key_cached_value(webhook_router):
    """Test get api key cached value."""
    webhook_router.api_key_cache['value'] = 'cached-key'
    result = webhook_router.get_api_key()
    assert result == 'cached-key'



@patch('boto3.client')
def test_get_api_key_missing_env_var_raises_runtime_error(_mock_boto_client, webhook_router):
    """Test get api key missing env var raises runtime error."""
    webhook_router.api_key_cache['value'] = None
    raised_error = None
    with patch.dict('os.environ', {}, clear=True):
        try:
            webhook_router.get_api_key()
        except RuntimeError as e:
            raised_error = e
    assert raised_error is not None


@patch('boto3.client')
def test_get_api_key_missing_env_var_error_mentions_parameter_name(
    _mock_boto_client,
    webhook_router
):
    """Test get api key missing env var error mentions parameter name."""
    webhook_router.api_key_cache['value'] = None
    raised_error = None
    with patch.dict('os.environ', {}, clear=True):
        try:
            webhook_router.get_api_key()
        except RuntimeError as e:
            raised_error = e
    assert 'API_KEY_PARAMETER_NAME' in str(raised_error)



def test_route_runner_request_ssm_failure(webhook_router, config):
    """Test route runner request ssm failure."""
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    with patch('boto3.client'):
        with patch.object(webhook_router, 'get_api_key', side_effect=RuntimeError('SSM error')):
            with patch.dict('os.environ', {'API_BASE_URL': 'https://api.test.com'}):
                result = webhook_router.route_runner_request(123, config['ec2'], 'test/repo')
                assert result['success'] is False



@patch('boto3.client')
def test_enqueue_job_sqs_send_failure(mock_boto_client, webhook_router):
    """Test enqueue job sqs send failure."""
    mock_sqs = MagicMock()
    mock_sqs.send_message.side_effect = ClientError({'Error': {'Code': 'TestError'}}, 'SendMessage')
    mock_boto_client.return_value = mock_sqs
    with patch.dict('os.environ', {'JOB_QUEUE_URL': 'https://sqs.test.com/queue'}):
        result = webhook_router.enqueue_job({'job_id': 123})
        assert result['success'] is False



def test_check_and_record_idempotency_missing_table(webhook_router):
    """Test check and record idempotency missing table."""
    with patch.dict('os.environ', {}, clear=True):
        result = webhook_router.check_and_record_idempotency('test-id')
        assert result is False



@patch('boto3.client')
def test_check_and_record_idempotency_dynamodb_error(mock_boto_client, webhook_router):
    """Test check and record idempotency dynamodb error."""
    mock_dynamodb = MagicMock()
    err = ClientError({'Error': {'Code': 'ServiceUnavailable'}}, 'PutItem')
    mock_dynamodb.put_item.side_effect = err
    mock_boto_client.return_value = mock_dynamodb
    with patch.dict('os.environ', {'IDEMPOTENCY_TABLE_NAME': 'test-table'}):
        result = webhook_router.check_and_record_idempotency('test-id')
        assert result is False



def test_handle_api_gateway_event_missing_signature(webhook_router):
    """Test handle api gateway event missing signature."""
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
    """Test publish metric cloudwatch failure."""
    mock_cw = MagicMock()
    err = ClientError({'Error': {'Code': 'TestError'}}, 'PutMetricData')
    mock_cw.put_metric_data.side_effect = err
    mock_boto_client.return_value = mock_cw
    webhook_router.publish_metric('TestMetric', 1.0)
    assert True





def test_verify_signature_with_valid_signature_returns_true(webhook_router):
    """Test verify signature with valid signature returns true."""
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
    """Test verify signature with invalid signature returns false."""
    secret = 'test-secret'
    payload = 'test payload'
    header = 'sha256=invalid'
    result = webhook_router.verify_signature(payload, header, secret)
    assert result is False



def test_verify_signature_with_empty_header_returns_false(webhook_router):
    """Test verify signature with empty header returns false."""
    result = webhook_router.verify_signature('payload', '', 'secret')
    assert result is False



def test_verify_signature_with_malformed_header_returns_false(webhook_router):
    """Test verify signature with malformed header returns false."""
    result = webhook_router.verify_signature('payload', 'malformed', 'secret')
    assert result is False



def test_lambda_handler_options_request_returns_200(webhook_router, lambda_context):
    """Test lambda handler options request returns 200."""
    event = {'path': '/v1/runners', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)



def test_lambda_handler_options_request_returns_allow_origin_header(webhook_router, lambda_context):
    """Test lambda handler options request returns allow origin header."""
    event = {'path': '/v1/runners', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    assert 'Access-Control-Allow-Origin' in headers


def test_lambda_handler_options_request_returns_allow_methods_header(
    webhook_router,
    lambda_context
):
    """Test lambda handler options request returns allow methods header."""
    event = {'path': '/v1/runners', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    assert 'Access-Control-Allow-Methods' in headers


def test_lambda_handler_options_request_returns_allow_headers_header(
    webhook_router,
    lambda_context
):
    """Test lambda handler options request returns allow headers header."""
    event = {'path': '/v1/runners', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    assert 'Access-Control-Allow-Headers' in headers



def test_lambda_handler_options_request_allows_wildcard_origin(webhook_router, lambda_context):
    """Test lambda handler options request allows wildcard origin."""
    event = {'path': '/v1/runners', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    assert headers['Access-Control-Allow-Origin'] == '*'



def test_lambda_handler_options_request_allows_get_method(webhook_router, lambda_context):
    """Test lambda handler options request allows get method."""
    event = {'path': '/v1/runners', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    allowed_methods = headers['Access-Control-Allow-Methods']
    assert 'GET' in allowed_methods


def test_lambda_handler_options_request_allows_post_method(webhook_router, lambda_context):
    """Test lambda handler options request allows post method."""
    event = {'path': '/v1/runners', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    allowed_methods = headers['Access-Control-Allow-Methods']
    assert 'POST' in allowed_methods


def test_lambda_handler_options_request_allows_options_method(webhook_router, lambda_context):
    """Test lambda handler options request allows options method."""
    event = {'path': '/v1/runners', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = webhook_router.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    allowed_methods = headers['Access-Control-Allow-Methods']
    assert 'OPTIONS' in allowed_methods


def test_should_record_circuit_breaker_failure_returns_false_for_503(webhook_router):
    """Test should record circuit breaker failure returns false for 503."""
    assert webhook_router.should_record_circuit_breaker_failure(503) is False


def test_should_record_circuit_breaker_failure_returns_true_for_500(webhook_router):
    """Test should record circuit breaker failure returns true for 500."""
    assert webhook_router.should_record_circuit_breaker_failure(500) is True


def test_should_record_circuit_breaker_failure_returns_true_for_502(webhook_router):
    """Test should record circuit breaker failure returns true for 502."""
    assert webhook_router.should_record_circuit_breaker_failure(502) is True


def test_should_record_circuit_breaker_failure_returns_true_for_504(webhook_router):
    """Test should record circuit breaker failure returns true for 504."""
    assert webhook_router.should_record_circuit_breaker_failure(504) is True


def test_should_record_circuit_breaker_failure_returns_false_for_400(webhook_router):
    """Test should record circuit breaker failure returns false for 400."""
    assert webhook_router.should_record_circuit_breaker_failure(400) is False


def test_should_record_circuit_breaker_failure_returns_false_for_200(webhook_router):
    """Test should record circuit breaker failure returns false for 200."""
    assert webhook_router.should_record_circuit_breaker_failure(200) is False


def test_should_record_circuit_breaker_failure_returns_true_for_none(webhook_router):
    """Test should record circuit breaker failure returns true for none."""
    assert webhook_router.should_record_circuit_breaker_failure(None) is True
