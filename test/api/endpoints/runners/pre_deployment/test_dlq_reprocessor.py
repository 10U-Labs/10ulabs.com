import json
import urllib.error
from unittest.mock import patch, MagicMock, Mock

from botocore.exceptions import ClientError


def test_get_sqs_client_returns_client(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = MagicMock()
        result = dlq_reprocessor.get_sqs_client()
        assert result is not None


def test_get_sqs_client_caches_client(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = MagicMock()
        dlq_reprocessor.get_sqs_client()
        dlq_reprocessor.get_sqs_client()
        assert mock_boto.call_count == 1


def test_get_sns_client_returns_client(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = MagicMock()
        result = dlq_reprocessor.get_sns_client()
        assert result is not None


def test_get_sns_client_caches_client(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = MagicMock()
        dlq_reprocessor.get_sns_client()
        dlq_reprocessor.get_sns_client()
        assert mock_boto.call_count == 1


def test_get_ssm_client_returns_client(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = MagicMock()
        result = dlq_reprocessor.get_ssm_client()
        assert result is not None


def test_get_ssm_client_caches_client(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = MagicMock()
        dlq_reprocessor.get_ssm_client()
        dlq_reprocessor.get_ssm_client()
        assert mock_boto.call_count == 1


def test_get_github_token_returns_empty_when_no_parameter_name(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    with patch.dict('os.environ', {}, clear=True):
        result = dlq_reprocessor.get_github_token()
        assert result == ''


def test_get_github_token_returns_token_from_ssm(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-github-token'}}
    with patch.dict('os.environ', {'GITHUB_TOKEN_PARAMETER_NAME': '/test/github/token'}):
        with patch.object(dlq_reprocessor, 'get_ssm_client', return_value=mock_ssm):
            result = dlq_reprocessor.get_github_token()
            assert result == 'test-github-token'


def test_get_github_token_calls_ssm_with_decryption(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
    with patch.dict('os.environ', {'GITHUB_TOKEN_PARAMETER_NAME': '/test/param'}):
        with patch.object(dlq_reprocessor, 'get_ssm_client', return_value=mock_ssm):
            dlq_reprocessor.get_github_token()
            mock_ssm.get_parameter.assert_called_once_with(Name='/test/param', WithDecryption=True)


def test_get_github_token_returns_empty_on_client_error(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.side_effect = ClientError(
        {'Error': {'Code': 'ParameterNotFound', 'Message': 'Not found'}},
        'GetParameter'
    )
    with patch.dict('os.environ', {'GITHUB_TOKEN_PARAMETER_NAME': '/test/param'}):
        with patch.object(dlq_reprocessor, 'get_ssm_client', return_value=mock_ssm):
            result = dlq_reprocessor.get_github_token()
            assert result == ''


def test_check_github_job_status_returns_unknown_when_no_token(dlq_reprocessor):
    result = dlq_reprocessor.check_github_job_status('owner/repo', 123, '')
    assert result == 'unknown'


def test_check_github_job_status_returns_status_from_api(dlq_reprocessor):
    mock_response = Mock()
    mock_response.read.return_value = json.dumps({'status': 'completed'}).encode()
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = dlq_reprocessor.check_github_job_status('owner/repo', 123, 'test-token')
        assert result == 'completed'


def test_check_github_job_status_returns_unknown_when_status_missing(dlq_reprocessor):
    mock_response = Mock()
    mock_response.read.return_value = json.dumps({}).encode()
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = dlq_reprocessor.check_github_job_status('owner/repo', 123, 'test-token')
        assert result == 'unknown'


def test_check_github_job_status_returns_not_found_on_404(dlq_reprocessor):
    http_error = urllib.error.HTTPError(
        'https://api.github.com/repos/owner/repo/actions/jobs/123',
        404, 'Not Found', {}, None
    )
    with patch('urllib.request.urlopen', side_effect=http_error):
        result = dlq_reprocessor.check_github_job_status('owner/repo', 123, 'test-token')
        assert result == 'not_found'


def test_check_github_job_status_returns_error_on_other_http_error(dlq_reprocessor):
    http_error = urllib.error.HTTPError(
        'https://api.github.com/repos/owner/repo/actions/jobs/123',
        500, 'Server Error', {}, None
    )
    with patch('urllib.request.urlopen', side_effect=http_error):
        result = dlq_reprocessor.check_github_job_status('owner/repo', 123, 'test-token')
        assert result == 'error'


def test_check_github_job_status_returns_error_on_url_error(dlq_reprocessor):
    url_error = urllib.error.URLError('Connection refused')
    with patch('urllib.request.urlopen', side_effect=url_error):
        result = dlq_reprocessor.check_github_job_status('owner/repo', 123, 'test-token')
        assert result == 'error'


def test_check_github_job_status_returns_error_on_value_error(dlq_reprocessor):
    mock_response = Mock()
    mock_response.read.return_value = b'not json'
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = dlq_reprocessor.check_github_job_status('owner/repo', 123, 'test-token')
        assert result == 'error'


def test_send_poison_pill_alert_does_nothing_when_no_sns_topic_arn(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sns = MagicMock()
    with patch.dict('os.environ', {}, clear=True):
        with patch.object(dlq_reprocessor, 'get_sns_client', return_value=mock_sns):
            dlq_reprocessor.send_poison_pill_alert({'job_id': 123}, 4, 'test reason')
            mock_sns.publish.assert_not_called()


def test_send_poison_pill_alert_publishes_to_sns(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sns = MagicMock()
    with patch.dict('os.environ', {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:test-topic'}):
        with patch.object(dlq_reprocessor, 'get_sns_client', return_value=mock_sns):
            dlq_reprocessor.send_poison_pill_alert({'job_id': 456, 'github_repo': 'owner/repo'}, 4, 'max retries')
            assert mock_sns.publish.called


def test_send_poison_pill_alert_uses_correct_topic_arn(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sns = MagicMock()
    expected_arn = 'arn:aws:sns:us-east-1:123456789012:alert-topic'
    with patch.dict('os.environ', {'SNS_TOPIC_ARN': expected_arn}):
        with patch.object(dlq_reprocessor, 'get_sns_client', return_value=mock_sns):
            dlq_reprocessor.send_poison_pill_alert({'job_id': 789}, 5, 'test')
            call_kwargs = mock_sns.publish.call_args[1]
            assert call_kwargs['TopicArn'] == expected_arn


def test_send_poison_pill_alert_includes_job_id_in_subject(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sns = MagicMock()
    with patch.dict('os.environ', {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:topic'}):
        with patch.object(dlq_reprocessor, 'get_sns_client', return_value=mock_sns):
            dlq_reprocessor.send_poison_pill_alert({'job_id': 999}, 4, 'test')
            call_kwargs = mock_sns.publish.call_args[1]
            assert '999' in call_kwargs['Subject']


def test_send_poison_pill_alert_handles_client_error(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sns = MagicMock()
    mock_sns.publish.side_effect = ClientError(
        {'Error': {'Code': 'InvalidParameter', 'Message': 'Error'}},
        'Publish'
    )
    with patch.dict('os.environ', {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:topic'}):
        with patch.object(dlq_reprocessor, 'get_sns_client', return_value=mock_sns):
            dlq_reprocessor.send_poison_pill_alert({'job_id': 111}, 4, 'test')
            assert mock_sns.publish.called


def test_get_reprocess_attempt_count_returns_zero_for_empty_message(dlq_reprocessor):
    result = dlq_reprocessor.get_reprocess_attempt_count({})
    assert result == 0


def test_get_reprocess_attempt_count_returns_zero_when_no_attributes(dlq_reprocessor):
    message = {'MessageAttributes': {}}
    result = dlq_reprocessor.get_reprocess_attempt_count(message)
    assert result == 0


def test_get_reprocess_attempt_count_returns_zero_when_no_reprocess_attempts(dlq_reprocessor):
    message = {'MessageAttributes': {'OtherAttr': {'StringValue': '5'}}}
    result = dlq_reprocessor.get_reprocess_attempt_count(message)
    assert result == 0


def test_get_reprocess_attempt_count_returns_value_from_attribute(dlq_reprocessor):
    message = {
        'MessageAttributes': {
            'ReprocessAttempts': {'DataType': 'Number', 'StringValue': '3'}
        }
    }
    result = dlq_reprocessor.get_reprocess_attempt_count(message)
    assert result == 3


def test_get_reprocess_attempt_count_returns_zero_for_invalid_value(dlq_reprocessor):
    message = {
        'MessageAttributes': {
            'ReprocessAttempts': {'DataType': 'Number', 'StringValue': 'invalid'}
        }
    }
    result = dlq_reprocessor.get_reprocess_attempt_count(message)
    assert result == 0


def test_reprocess_dlq_messages_returns_dict_with_reprocessed_key(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {'Messages': []}
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value=''):
            result = dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
            assert 'reprocessed' in result


def test_reprocess_dlq_messages_returns_dict_with_skipped_completed_key(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {'Messages': []}
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value=''):
            result = dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
            assert 'skipped_completed' in result


def test_reprocess_dlq_messages_returns_dict_with_skipped_max_retries_key(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {'Messages': []}
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value=''):
            result = dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
            assert 'skipped_max_retries' in result


def test_reprocess_dlq_messages_returns_dict_with_failed_key(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {'Messages': []}
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value=''):
            result = dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
            assert 'failed' in result


def test_reprocess_dlq_messages_increments_failed_for_invalid_json(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {
        'Messages': [{
            'MessageId': 'msg-1',
            'ReceiptHandle': 'handle-1',
            'Body': 'not valid json',
            'MessageAttributes': {}
        }]
    }
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value=''):
            result = dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
            assert result['failed'] == 1


def test_reprocess_dlq_messages_skips_message_exceeding_max_attempts(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {
        'Messages': [{
            'MessageId': 'msg-1',
            'ReceiptHandle': 'handle-1',
            'Body': json.dumps({'job_id': 123, 'github_repo': 'owner/repo'}),
            'MessageAttributes': {
                'ReprocessAttempts': {'DataType': 'Number', 'StringValue': '3'}
            }
        }]
    }
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value=''):
            with patch.object(dlq_reprocessor, 'send_poison_pill_alert'):
                result = dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
                assert result['skipped_max_retries'] == 1


def test_reprocess_dlq_messages_sends_alert_for_max_retries(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {
        'Messages': [{
            'MessageId': 'msg-1',
            'ReceiptHandle': 'handle-1',
            'Body': json.dumps({'job_id': 123, 'github_repo': 'owner/repo'}),
            'MessageAttributes': {
                'ReprocessAttempts': {'DataType': 'Number', 'StringValue': '3'}
            }
        }]
    }
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value=''):
            with patch.object(dlq_reprocessor, 'send_poison_pill_alert') as mock_alert:
                dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
                assert mock_alert.called


def test_reprocess_dlq_messages_deletes_completed_jobs(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {
        'Messages': [{
            'MessageId': 'msg-1',
            'ReceiptHandle': 'handle-1',
            'Body': json.dumps({'job_id': 123, 'github_repo': 'owner/repo'}),
            'MessageAttributes': {}
        }]
    }
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value='test-token'):
            with patch.object(dlq_reprocessor, 'check_github_job_status', return_value='completed'):
                result = dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
                assert result['skipped_completed'] == 1


def test_reprocess_dlq_messages_deletes_not_found_jobs(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {
        'Messages': [{
            'MessageId': 'msg-1',
            'ReceiptHandle': 'handle-1',
            'Body': json.dumps({'job_id': 456, 'github_repo': 'owner/repo'}),
            'MessageAttributes': {}
        }]
    }
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value='test-token'):
            with patch.object(dlq_reprocessor, 'check_github_job_status', return_value='not_found'):
                result = dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
                assert result['skipped_completed'] == 1


def test_reprocess_dlq_messages_reprocesses_queued_jobs(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {
        'Messages': [{
            'MessageId': 'msg-1',
            'ReceiptHandle': 'handle-1',
            'Body': json.dumps({'job_id': 789, 'github_repo': 'owner/repo'}),
            'MessageAttributes': {}
        }]
    }
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value='test-token'):
            with patch.object(dlq_reprocessor, 'check_github_job_status', return_value='queued'):
                result = dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
                assert result['reprocessed'] == 1


def test_reprocess_dlq_messages_adds_reprocess_attempts_attribute(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {
        'Messages': [{
            'MessageId': 'msg-1',
            'ReceiptHandle': 'handle-1',
            'Body': json.dumps({'job_id': 111, 'github_repo': 'owner/repo'}),
            'MessageAttributes': {}
        }]
    }
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value='test-token'):
            with patch.object(dlq_reprocessor, 'check_github_job_status', return_value='queued'):
                dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
                call_kwargs = mock_sqs.send_message.call_args[1]
                assert call_kwargs['MessageAttributes']['ReprocessAttempts']['StringValue'] == '1'


def test_reprocess_dlq_messages_increments_existing_reprocess_attempts(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {
        'Messages': [{
            'MessageId': 'msg-1',
            'ReceiptHandle': 'handle-1',
            'Body': json.dumps({'job_id': 222, 'github_repo': 'owner/repo'}),
            'MessageAttributes': {
                'ReprocessAttempts': {'DataType': 'Number', 'StringValue': '2'}
            }
        }]
    }
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value='test-token'):
            with patch.object(dlq_reprocessor, 'check_github_job_status', return_value='queued'):
                dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
                call_kwargs = mock_sqs.send_message.call_args[1]
                assert call_kwargs['MessageAttributes']['ReprocessAttempts']['StringValue'] == '3'


def test_reprocess_dlq_messages_returns_error_on_receive_failure(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Error'}},
        'ReceiveMessage'
    )
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value=''):
            result = dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
            assert 'error' in result


def test_reprocess_dlq_messages_handles_send_message_failure(dlq_reprocessor):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {
        'Messages': [{
            'MessageId': 'msg-1',
            'ReceiptHandle': 'handle-1',
            'Body': json.dumps({'job_id': 333, 'github_repo': 'owner/repo'}),
            'MessageAttributes': {}
        }]
    }
    mock_sqs.send_message.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Error'}},
        'SendMessage'
    )
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value='test-token'):
            with patch.object(dlq_reprocessor, 'check_github_job_status', return_value='queued'):
                result = dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
                assert result['failed'] == 1


def test_handler_returns_200_status_code(dlq_reprocessor, lambda_context):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {'Messages': []}
    with patch.dict('os.environ', {'JOB_DLQ_URL': 'job-dlq', 'JOB_QUEUE_URL': 'job-queue'}):
        with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
            with patch.object(dlq_reprocessor, 'get_github_token', return_value=''):
                result = dlq_reprocessor.handler({}, lambda_context)
                assert result['statusCode'] == 200


def test_handler_returns_json_body(dlq_reprocessor, lambda_context):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {'Messages': []}
    with patch.dict('os.environ', {'JOB_DLQ_URL': 'job-dlq', 'JOB_QUEUE_URL': 'job-queue'}):
        with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
            with patch.object(dlq_reprocessor, 'get_github_token', return_value=''):
                result = dlq_reprocessor.handler({}, lambda_context)
                body = json.loads(result['body'])
                assert 'job_dlq' in body


def test_handler_includes_webhook_dlq_note_when_configured(dlq_reprocessor, lambda_context):
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {'Messages': []}
    with patch.dict('os.environ', {'WEBHOOK_DLQ_URL': 'webhook-dlq', 'JOB_DLQ_URL': 'job-dlq', 'JOB_QUEUE_URL': 'job-queue'}):
        with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
            with patch.object(dlq_reprocessor, 'get_github_token', return_value=''):
                result = dlq_reprocessor.handler({}, lambda_context)
                body = json.loads(result['body'])
                assert 'webhook_dlq' in body
