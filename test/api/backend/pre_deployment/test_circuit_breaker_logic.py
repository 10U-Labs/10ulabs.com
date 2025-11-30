import json
import time
from unittest.mock import patch, MagicMock
from test.api.backend.pre_deployment.conftest import parse_response_body, assert_response_status, assert_no_hardcoded_env_defaults, get_lambda_path

from botocore.exceptions import ClientError


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



def test_circuit_breaker_concurrent_failures_increment_count(webhook_router):
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 0
    webhook_router.record_circuit_breaker_failure()
    webhook_router.record_circuit_breaker_failure()
    assert webhook_router.circuit_breaker_state['failures'] == 2



def test_circuit_breaker_concurrent_success_resets_failures(webhook_router):
    webhook_router.circuit_breaker_state['state'] = 'closed'
    webhook_router.circuit_breaker_state['failures'] = 4
    webhook_router.record_circuit_breaker_success()
    assert webhook_router.circuit_breaker_state['failures'] == 0



def test_circuit_breaker_half_open_allows_one_request(webhook_router):
    webhook_router.circuit_breaker_state['state'] = 'open'
    webhook_router.circuit_breaker_state['last_failure_time'] = time.time() - 61
    with patch('boto3.client'):
        result = webhook_router.check_circuit_breaker()
    assert result is True



def test_circuit_breaker_state_remains_open_before_timeout(webhook_router):
    webhook_router.circuit_breaker_state['state'] = 'open'
    webhook_router.circuit_breaker_state['last_failure_time'] = time.time() - 30
    with patch('boto3.client'):
        result = webhook_router.check_circuit_breaker()
    assert result is False



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



def test_no_hardcoded_defaults_in_dlq_reprocessor():
    assert_no_hardcoded_env_defaults(get_lambda_path("dlq_reprocessor.py"))



def test_no_hardcoded_defaults_in_circuit_breaker_remediation():
    assert_no_hardcoded_env_defaults(get_lambda_path("circuit_breaker_remediation.py"))



@patch('boto3.client')
@patch.dict('os.environ', {
    'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-queue',
    'WEBHOOK_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/webhook-dlq',
    'JOB_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-dlq'
})

def test_dlq_reprocessor_with_all_env_vars(mock_boto_client, dlq_reprocessor, lambda_context):
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {'Messages': []}
    mock_boto_client.return_value = mock_sqs
    response = dlq_reprocessor.handler({}, lambda_context)
    assert response['statusCode'] == 200


@patch('boto3.client')
@patch.dict('os.environ', {
    'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-queue',
    'WEBHOOK_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/webhook-dlq',
    'JOB_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-dlq'
})

def test_dlq_reprocessor_processes_job_dlq_messages(mock_boto_client, dlq_reprocessor, lambda_context):
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {
        'Messages': [
            {'Body': '{"test": "data"}', 'ReceiptHandle': 'handle1', 'MessageAttributes': {}}
        ]
    }
    mock_sqs.send_message.return_value = {'MessageId': 'msg1'}
    mock_sqs.delete_message.return_value = {}
    mock_boto_client.return_value = mock_sqs
    response = dlq_reprocessor.handler({}, lambda_context)
    body = json.loads(response['body'])
    assert body['job_dlq']['reprocessed'] == 1


@patch('boto3.client')
@patch.dict('os.environ', {
    'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-queue',
    'WEBHOOK_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/webhook-dlq',
    'JOB_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-dlq'
})

def test_dlq_reprocessor_deletes_messages_after_reprocessing(mock_boto_client, dlq_reprocessor, lambda_context):
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {
        'Messages': [
            {'Body': '{"test": "data"}', 'ReceiptHandle': 'handle1', 'MessageAttributes': {}}
        ]
    }
    mock_sqs.send_message.return_value = {'MessageId': 'msg1'}
    mock_sqs.delete_message.return_value = {}
    mock_boto_client.return_value = mock_sqs
    dlq_reprocessor.handler({}, lambda_context)
    assert mock_sqs.delete_message.called


@patch('boto3.client')
@patch.dict('os.environ', {
    'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-queue',
    'WEBHOOK_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/webhook-dlq',
    'JOB_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-dlq'
})

def test_dlq_reprocessor_handles_send_message_failure(mock_boto_client, dlq_reprocessor, lambda_context):
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {
        'Messages': [
            {'Body': '{"test": "data"}', 'ReceiptHandle': 'handle1', 'MessageAttributes': {}}
        ]
    }
    mock_sqs.send_message.side_effect = ClientError({'Error': {'Code': 'ServiceUnavailable', 'Message': 'Test error'}}, 'SendMessage')
    mock_boto_client.return_value = mock_sqs
    response = dlq_reprocessor.handler({}, lambda_context)
    body = json.loads(response['body'])
    assert body['job_dlq']['failed'] == 1


@patch('boto3.client')
@patch.dict('os.environ', {
    'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-queue',
    'WEBHOOK_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/webhook-dlq',
    'JOB_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-dlq'
})

def test_dlq_reprocessor_handles_receive_message_failure(mock_boto_client, dlq_reprocessor, lambda_context):
    mock_sqs = MagicMock()
    mock_sqs.receive_message.side_effect = ClientError({'Error': {'Code': 'ServiceUnavailable', 'Message': 'Test error'}}, 'ReceiveMessage')
    mock_boto_client.return_value = mock_sqs
    response = dlq_reprocessor.handler({}, lambda_context)
    body = json.loads(response['body'])
    assert 'error' in body['job_dlq']


@patch('boto3.client')
@patch.dict('os.environ', {
    'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-queue',
    'WEBHOOK_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/webhook-dlq',
    'JOB_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-dlq'
})

def test_dlq_reprocessor_webhook_dlq_returns_manual_intervention_note(mock_boto_client, dlq_reprocessor, lambda_context):
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {'Messages': []}
    mock_boto_client.return_value = mock_sqs
    response = dlq_reprocessor.handler({}, lambda_context)
    body = json.loads(response['body'])
    assert body['webhook_dlq']['note'] == 'Manual intervention required'


@patch('boto3.client')
@patch.dict('os.environ', {
    'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-queue',
    'WEBHOOK_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/webhook-dlq',
    'JOB_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-dlq'
})

def test_dlq_reprocessor_reprocesses_multiple_messages(mock_boto_client, dlq_reprocessor, lambda_context):
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {
        'Messages': [
            {'Body': '{"test": "data1"}', 'ReceiptHandle': 'handle1', 'MessageAttributes': {}},
            {'Body': '{"test": "data2"}', 'ReceiptHandle': 'handle2', 'MessageAttributes': {}}
        ]
    }
    mock_sqs.send_message.return_value = {'MessageId': 'msg1'}
    mock_sqs.delete_message.return_value = {}
    mock_boto_client.return_value = mock_sqs
    response = dlq_reprocessor.handler({}, lambda_context)
    body = json.loads(response['body'])
    assert body['job_dlq']['reprocessed'] == 2


@patch('boto3.client')
@patch.dict('os.environ', {
    'JOB_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-queue',
    'WEBHOOK_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/webhook-dlq',
    'JOB_DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/job-dlq'
})

def test_dlq_reprocessor_preserves_message_attributes(mock_boto_client, dlq_reprocessor, lambda_context):
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {
        'Messages': [
            {'Body': '{"test": "data"}', 'ReceiptHandle': 'handle1', 'MessageAttributes': {'attr1': {'StringValue': 'value1'}}}
        ]
    }
    mock_sqs.send_message.return_value = {'MessageId': 'msg1'}
    mock_sqs.delete_message.return_value = {}
    mock_boto_client.return_value = mock_sqs
    dlq_reprocessor.handler({}, lambda_context)
    call_args = mock_sqs.send_message.call_args
    assert 'MessageAttributes' in call_args[1]
