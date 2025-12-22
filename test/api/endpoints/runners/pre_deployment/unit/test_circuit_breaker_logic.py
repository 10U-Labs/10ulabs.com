"""Unit tests for DLQ reprocessor and circuit breaker Python lambdas."""
import json
from contextlib import contextmanager
from unittest.mock import patch, MagicMock

from botocore.exceptions import ClientError

from .conftest import (
    parse_response_body,
    assert_response_status,
    assert_no_hardcoded_env_defaults,
    get_lambda_path,
)


DLQ_ENV = {
    'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-queue',
    'WEBHOOK_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/webhook-dlq',
    'JOB_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-dlq'
}

JOB_DLQ_ENV = {
    'JOB_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/job-dlq',
    'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/job-queue'
}


def _create_sqs_message(body='{"test": "data"}', handle='handle1', attrs=None):
    """Create a standard SQS message."""
    return {'Body': body, 'ReceiptHandle': handle, 'MessageAttributes': attrs or {}}


def _create_id_message(msg_id, handle_prefix='receipt'):
    """Create an SQS message with an id in the body."""
    return {
        'Body': json.dumps({'id': msg_id}),
        'ReceiptHandle': f'{handle_prefix}-{msg_id}',
        'MessageAttributes': {}
    }


def _create_id_messages(count):
    """Create multiple SQS messages with sequential ids."""
    return [_create_id_message(i) for i in range(1, count + 1)]


def _create_mock_sqs_with_messages(messages=None, send_error=None, receive_error=None):
    """Create a mock SQS client with configured responses."""
    mock_sqs = MagicMock()
    if receive_error:
        mock_sqs.receive_message.side_effect = receive_error
    else:
        mock_sqs.receive_message.return_value = {'Messages': messages or []}
    if send_error:
        mock_sqs.send_message.side_effect = send_error
    else:
        mock_sqs.send_message.return_value = {'MessageId': 'msg1'}
    mock_sqs.delete_message.return_value = {}
    return mock_sqs


@contextmanager
def _patched_dlq_handler(mock_sqs):
    """Context manager for patching DLQ handler with boto3 client."""
    with patch.dict('os.environ', DLQ_ENV):
        with patch('boto3.client', return_value=mock_sqs):
            yield


def test_handler_processes_job_dlq(dlq_reprocessor, dlq_message_factory, mock_sqs, lambda_context):
    """Test handler processes job dlq."""
    mock_sqs.receive_message.return_value = {
        'Messages': [dlq_message_factory(body={'job_id': 123})]
    }
    with patch.dict('os.environ', JOB_DLQ_ENV):
        response = dlq_reprocessor.handler({}, lambda_context)
    assert_response_status(response, 200)


def test_handler_returns_reprocessed_count(
    dlq_reprocessor,
    dlq_message_factory,
    mock_sqs,
    lambda_context
):
    """Test handler returns reprocessed count."""
    mock_sqs.receive_message.return_value = {
        'Messages': [dlq_message_factory(body={'job_id': 123})]
    }
    with patch.dict('os.environ', JOB_DLQ_ENV):
        response = dlq_reprocessor.handler({}, lambda_context)
    body = parse_response_body(response)
    assert body['job_dlq']['reprocessed'] == 1



def test_handler_handles_webhook_dlq_with_note(dlq_reprocessor, lambda_context):
    """Test handler handles webhook dlq with note."""
    event = {}
    with patch.dict('os.environ', {
        'WEBHOOK_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/webhook-dlq'
    }):
        response = dlq_reprocessor.handler(event, lambda_context)
        body = parse_response_body(response)
    assert 'note' in body['webhook_dlq']



def test_handler_skips_job_dlq_when_not_configured(dlq_reprocessor, lambda_context):
    """Test handler skips job dlq when not configured."""
    event = {}
    with patch.dict('os.environ', {}, clear=True):
        response = dlq_reprocessor.handler(event, lambda_context)
        body = parse_response_body(response)
    assert 'job_dlq' not in body



def test_handler_skips_webhook_dlq_when_not_configured(dlq_reprocessor, lambda_context):
    """Test handler skips webhook dlq when not configured."""
    event = {}
    with patch.dict('os.environ', {}, clear=True):
        response = dlq_reprocessor.handler(event, lambda_context)
        body = parse_response_body(response)
    assert 'webhook_dlq' not in body



def test_reprocess_dlq_messages_receives_messages(dlq_reprocessor, mock_sqs):
    """Test reprocess dlq messages receives messages."""
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
    """Test reprocess dlq messages sends to target queue."""
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
    """Test reprocess dlq messages deletes from dlq."""
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
    """Test reprocess dlq messages handles empty queue."""
    mock_sqs.receive_message.return_value = {}
    result = dlq_reprocessor.reprocess_dlq_messages(
        'https://sqs.us-east-1.amazonaws.com/123456789012/dlq',
        'https://sqs.us-east-1.amazonaws.com/123456789012/target'
    )
    assert result['reprocessed'] == 0



def test_reprocess_dlq_messages_processes_multiple_messages(dlq_reprocessor, mock_sqs):
    """Test reprocess dlq messages processes multiple messages."""
    mock_sqs.receive_message.return_value = {'Messages': _create_id_messages(3)}
    result = dlq_reprocessor.reprocess_dlq_messages(
        'https://sqs.us-east-1.amazonaws.com/123456789012/dlq',
        'https://sqs.us-east-1.amazonaws.com/123456789012/target'
    )
    assert result['reprocessed'] == 3



def test_reprocess_dlq_messages_counts_failures(dlq_reprocessor, mock_sqs):
    """Test reprocess dlq messages counts failures."""
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
    """Test reprocess dlq messages respects max messages limit."""
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
    """Test reprocess dlq messages preserves message attributes."""
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
    """Test reprocess dlq messages handles receive error."""
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
    """Test reprocess dlq messages continues on individual failure."""
    mock_sqs.receive_message.return_value = {'Messages': _create_id_messages(2)}
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
    """Test reprocess dlq messages uses long polling."""
    mock_sqs.receive_message.return_value = {}
    dlq_reprocessor.reprocess_dlq_messages(
        'https://sqs.us-east-1.amazonaws.com/123456789012/dlq',
        'https://sqs.us-east-1.amazonaws.com/123456789012/target'
    )
    call_args = mock_sqs.receive_message.call_args
    assert call_args[1]['WaitTimeSeconds'] == 5



def test_no_hardcoded_defaults_in_dlq_reprocessor():
    """Test no hardcoded defaults in dlq reprocessor."""
    assert_no_hardcoded_env_defaults(get_lambda_path("dlq_reprocessor.py"))



def test_no_hardcoded_defaults_in_circuit_breaker_remediation():
    """Test no hardcoded defaults in circuit breaker remediation."""
    assert_no_hardcoded_env_defaults(get_lambda_path("circuit_breaker_remediation.py"))



def test_dlq_reprocessor_with_all_env_vars(dlq_reprocessor, lambda_context):
    """Test dlq reprocessor with all env vars."""
    mock_sqs = _create_mock_sqs_with_messages([])
    with _patched_dlq_handler(mock_sqs):
        response = dlq_reprocessor.handler({}, lambda_context)
    assert response['statusCode'] == 200


def test_dlq_reprocessor_processes_job_dlq_messages(dlq_reprocessor, lambda_context):
    """Test dlq reprocessor processes job dlq messages."""
    mock_sqs = _create_mock_sqs_with_messages([_create_sqs_message()])
    with _patched_dlq_handler(mock_sqs):
        response = dlq_reprocessor.handler({}, lambda_context)
    body = json.loads(response['body'])
    assert body['job_dlq']['reprocessed'] == 1


def test_dlq_reprocessor_deletes_messages_after_reprocessing(dlq_reprocessor, lambda_context):
    """Test dlq reprocessor deletes messages after reprocessing."""
    mock_sqs = _create_mock_sqs_with_messages([_create_sqs_message()])
    with _patched_dlq_handler(mock_sqs):
        dlq_reprocessor.handler({}, lambda_context)
    assert mock_sqs.delete_message.called


def test_dlq_reprocessor_handles_send_message_failure(dlq_reprocessor, lambda_context):
    """Test dlq reprocessor handles send message failure."""
    err = ClientError(
        {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Test error'}}, 'SendMessage'
    )
    mock_sqs = _create_mock_sqs_with_messages([_create_sqs_message()], send_error=err)
    with _patched_dlq_handler(mock_sqs):
        response = dlq_reprocessor.handler({}, lambda_context)
    body = json.loads(response['body'])
    assert body['job_dlq']['failed'] == 1


def test_dlq_reprocessor_handles_receive_message_failure(dlq_reprocessor, lambda_context):
    """Test dlq reprocessor handles receive message failure."""
    err = ClientError(
        {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Test error'}}, 'ReceiveMessage'
    )
    mock_sqs = _create_mock_sqs_with_messages(receive_error=err)
    with _patched_dlq_handler(mock_sqs):
        response = dlq_reprocessor.handler({}, lambda_context)
    body = json.loads(response['body'])
    assert 'error' in body['job_dlq']


def test_dlq_reprocessor_webhook_dlq_returns_manual_intervention_note(
    dlq_reprocessor, lambda_context
):
    """Test dlq reprocessor webhook dlq returns manual intervention note."""
    mock_sqs = _create_mock_sqs_with_messages([])
    with _patched_dlq_handler(mock_sqs):
        response = dlq_reprocessor.handler({}, lambda_context)
    body = json.loads(response['body'])
    assert body['webhook_dlq']['note'] == 'Manual intervention required'


def test_dlq_reprocessor_reprocesses_multiple_messages(dlq_reprocessor, lambda_context):
    """Test dlq reprocessor reprocesses multiple messages."""
    messages = [
        _create_sqs_message(body='{"test": "data1"}', handle='handle1'),
        _create_sqs_message(body='{"test": "data2"}', handle='handle2')
    ]
    mock_sqs = _create_mock_sqs_with_messages(messages)
    with _patched_dlq_handler(mock_sqs):
        response = dlq_reprocessor.handler({}, lambda_context)
    body = json.loads(response['body'])
    assert body['job_dlq']['reprocessed'] == 2


def test_dlq_reprocessor_preserves_message_attributes(dlq_reprocessor, lambda_context):
    """Test dlq reprocessor preserves message attributes."""
    attrs = {'attr1': {'StringValue': 'value1'}}
    mock_sqs = _create_mock_sqs_with_messages([_create_sqs_message(attrs=attrs)])
    with _patched_dlq_handler(mock_sqs):
        dlq_reprocessor.handler({}, lambda_context)
    call_args = mock_sqs.send_message.call_args
    assert 'MessageAttributes' in call_args[1]
