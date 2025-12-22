"""Unit tests for test dlq reprocessor."""
import json
import urllib.error
from unittest.mock import patch, MagicMock

from botocore.exceptions import ClientError

from urllib_mocks import create_mock_urllib_response


def _create_sqs_with_empty_response(dlq_reprocessor):
    """Create mock SQS returning empty messages and run reprocess."""
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {'Messages': []}
    return mock_sqs


def _run_reprocess_empty(dlq_reprocessor, mock_sqs):
    """Run reprocess_dlq_messages with patched empty SQS and no github token."""
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value=''):
            return dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')


def _create_message_with_job(job_id, attrs=None):
    """Create an SQS message body with a job_id."""
    return {
        'MessageId': 'msg-1',
        'ReceiptHandle': 'handle-1',
        'Body': json.dumps({'job_id': job_id, 'github_repo': 'owner/repo'}),
        'MessageAttributes': attrs or {}
    }


def _create_sqs_with_message(dlq_reprocessor, job_id, attrs=None):
    """Create mock SQS returning a single message with job_id."""
    dlq_reprocessor.reset_clients()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {
        'Messages': [_create_message_with_job(job_id, attrs)]
    }
    return mock_sqs


def _create_handler_test_env():
    """Create environment dict for handler tests."""
    return {'JOB_DLQ_URL': 'job-dlq', 'JOB_QUEUE_URL': 'job-queue'}


def _run_handler_with_empty_sqs(dlq_reprocessor, env, context):
    """Run handler with empty SQS responses."""
    mock_sqs = _create_sqs_with_empty_response(dlq_reprocessor)
    with patch.dict('os.environ', env):
        with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
            with patch.object(dlq_reprocessor, 'get_github_token', return_value=''):
                return dlq_reprocessor.handler({}, context)


def _run_reprocess_with_job_status(dlq_reprocessor, mock_sqs, job_status):
    """Run reprocess_dlq_messages with job status check."""
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value='test-token'):
            with patch.object(dlq_reprocessor, 'check_github_job_status', return_value=job_status):
                return dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url'), mock_sqs


def test_get_sqs_client_returns_client(dlq_reprocessor):
    """Test get sqs client returns client."""
    dlq_reprocessor.reset_clients()
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = MagicMock()
        result = dlq_reprocessor.get_sqs_client()
        assert result is not None


def test_get_sqs_client_caches_client(dlq_reprocessor):
    """Test get sqs client caches client."""
    dlq_reprocessor.reset_clients()
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = MagicMock()
        dlq_reprocessor.get_sqs_client()
        dlq_reprocessor.get_sqs_client()
        assert mock_boto.call_count == 1


def test_get_sns_client_returns_client(dlq_reprocessor):
    """Test get sns client returns client."""
    dlq_reprocessor.reset_clients()
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = MagicMock()
        result = dlq_reprocessor.get_sns_client()
        assert result is not None


def test_get_sns_client_caches_client(dlq_reprocessor):
    """Test get sns client caches client."""
    dlq_reprocessor.reset_clients()
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = MagicMock()
        dlq_reprocessor.get_sns_client()
        dlq_reprocessor.get_sns_client()
        assert mock_boto.call_count == 1


def test_get_ssm_client_returns_client(dlq_reprocessor):
    """Test get ssm client returns client."""
    dlq_reprocessor.reset_clients()
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = MagicMock()
        result = dlq_reprocessor.get_ssm_client()
        assert result is not None


def test_get_ssm_client_caches_client(dlq_reprocessor):
    """Test get ssm client caches client."""
    dlq_reprocessor.reset_clients()
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = MagicMock()
        dlq_reprocessor.get_ssm_client()
        dlq_reprocessor.get_ssm_client()
        assert mock_boto.call_count == 1


def test_get_github_token_returns_empty_when_no_parameter_name(dlq_reprocessor):
    """Test get github token returns empty when no parameter name."""
    dlq_reprocessor.reset_clients()
    with patch.dict('os.environ', {}, clear=True):
        result = dlq_reprocessor.get_github_token()
        assert result == ''


def test_get_github_token_returns_token_from_ssm(dlq_reprocessor):
    """Test get github token returns token from ssm."""
    dlq_reprocessor.reset_clients()
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-github-token'}}
    with patch.dict('os.environ', {'GITHUB_TOKEN_PARAMETER_NAME': '/test/github/token'}):
        with patch.object(dlq_reprocessor, 'get_ssm_client', return_value=mock_ssm):
            result = dlq_reprocessor.get_github_token()
            assert result == 'test-github-token'


def test_get_github_token_calls_ssm_with_decryption(dlq_reprocessor):
    """Test get github token calls ssm with decryption."""
    dlq_reprocessor.reset_clients()
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
    with patch.dict('os.environ', {'GITHUB_TOKEN_PARAMETER_NAME': '/test/param'}):
        with patch.object(dlq_reprocessor, 'get_ssm_client', return_value=mock_ssm):
            dlq_reprocessor.get_github_token()
            mock_ssm.get_parameter.assert_called_once_with(Name='/test/param', WithDecryption=True)


def test_get_github_token_returns_empty_on_client_error(dlq_reprocessor):
    """Test get github token returns empty on client error."""
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
    """Test check github job status returns unknown when no token."""
    result = dlq_reprocessor.check_github_job_status('owner/repo', 123, '')
    assert result == 'unknown'


def test_check_github_job_status_returns_status_from_api(dlq_reprocessor):
    """Test check github job status returns status from api."""
    mock_response = create_mock_urllib_response(json_data={'status': 'completed'})
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = dlq_reprocessor.check_github_job_status('owner/repo', 123, 'test-token')
        assert result == 'completed'


def test_check_github_job_status_returns_unknown_when_status_missing(dlq_reprocessor):
    """Test check github job status returns unknown when status missing."""
    mock_response = create_mock_urllib_response(json_data={})
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = dlq_reprocessor.check_github_job_status('owner/repo', 123, 'test-token')
        assert result == 'unknown'


def test_check_github_job_status_returns_not_found_on_404(dlq_reprocessor):
    """Test check github job status returns not found on 404."""
    http_error = urllib.error.HTTPError(
        'https://api.github.com/repos/owner/repo/actions/jobs/123',
        404, 'Not Found', {}, None
    )
    with patch('urllib.request.urlopen', side_effect=http_error):
        result = dlq_reprocessor.check_github_job_status('owner/repo', 123, 'test-token')
        assert result == 'not_found'


def test_check_github_job_status_returns_error_on_other_http_error(dlq_reprocessor):
    """Test check github job status returns error on other http error."""
    http_error = urllib.error.HTTPError(
        'https://api.github.com/repos/owner/repo/actions/jobs/123',
        500, 'Server Error', {}, None
    )
    with patch('urllib.request.urlopen', side_effect=http_error):
        result = dlq_reprocessor.check_github_job_status('owner/repo', 123, 'test-token')
        assert result == 'error'


def test_check_github_job_status_returns_error_on_url_error(dlq_reprocessor):
    """Test check github job status returns error on url error."""
    url_error = urllib.error.URLError('Connection refused')
    with patch('urllib.request.urlopen', side_effect=url_error):
        result = dlq_reprocessor.check_github_job_status('owner/repo', 123, 'test-token')
        assert result == 'error'


def test_check_github_job_status_returns_error_on_value_error(dlq_reprocessor):
    """Test check github job status returns error on value error."""
    mock_response = create_mock_urllib_response(read_value=b'not json')
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = dlq_reprocessor.check_github_job_status('owner/repo', 123, 'test-token')
        assert result == 'error'


def test_send_poison_pill_alert_does_nothing_when_no_sns_topic_arn(dlq_reprocessor):
    """Test send poison pill alert does nothing when no sns topic arn."""
    dlq_reprocessor.reset_clients()
    mock_sns = MagicMock()
    with patch.dict('os.environ', {}, clear=True):
        with patch.object(dlq_reprocessor, 'get_sns_client', return_value=mock_sns):
            dlq_reprocessor.send_poison_pill_alert({'job_id': 123}, 4, 'test reason')
            mock_sns.publish.assert_not_called()


def test_send_poison_pill_alert_publishes_to_sns(dlq_reprocessor):
    """Test send poison pill alert publishes to sns."""
    dlq_reprocessor.reset_clients()
    mock_sns = MagicMock()
    sns_arn = 'arn:aws:sns:us-east-1:123456789012:test-topic'
    with patch.dict('os.environ', {'SNS_TOPIC_ARN': sns_arn}):
        with patch.object(dlq_reprocessor, 'get_sns_client', return_value=mock_sns):
            message = {'job_id': 456, 'github_repo': 'owner/repo'}
            dlq_reprocessor.send_poison_pill_alert(message, 4, 'max retries')
            assert mock_sns.publish.called


def test_send_poison_pill_alert_uses_correct_topic_arn(dlq_reprocessor):
    """Test send poison pill alert uses correct topic arn."""
    dlq_reprocessor.reset_clients()
    mock_sns = MagicMock()
    expected_arn = 'arn:aws:sns:us-east-1:123456789012:alert-topic'
    with patch.dict('os.environ', {'SNS_TOPIC_ARN': expected_arn}):
        with patch.object(dlq_reprocessor, 'get_sns_client', return_value=mock_sns):
            dlq_reprocessor.send_poison_pill_alert({'job_id': 789}, 5, 'test')
            call_kwargs = mock_sns.publish.call_args[1]
            assert call_kwargs['TopicArn'] == expected_arn


def test_send_poison_pill_alert_includes_job_id_in_subject(dlq_reprocessor):
    """Test send poison pill alert includes job id in subject."""
    dlq_reprocessor.reset_clients()
    mock_sns = MagicMock()
    with patch.dict('os.environ', {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:topic'}):
        with patch.object(dlq_reprocessor, 'get_sns_client', return_value=mock_sns):
            dlq_reprocessor.send_poison_pill_alert({'job_id': 999}, 4, 'test')
            call_kwargs = mock_sns.publish.call_args[1]
            assert '999' in call_kwargs['Subject']


def test_send_poison_pill_alert_handles_client_error(dlq_reprocessor):
    """Test send poison pill alert handles client error."""
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
    """Test get reprocess attempt count returns zero for empty message."""
    result = dlq_reprocessor.get_reprocess_attempt_count({})
    assert result == 0


def test_get_reprocess_attempt_count_returns_zero_when_no_attributes(dlq_reprocessor):
    """Test get reprocess attempt count returns zero when no attributes."""
    message = {'MessageAttributes': {}}
    result = dlq_reprocessor.get_reprocess_attempt_count(message)
    assert result == 0


def test_get_reprocess_attempt_count_returns_zero_when_no_reprocess_attempts(dlq_reprocessor):
    """Test get reprocess attempt count returns zero when no reprocess attempts."""
    message = {'MessageAttributes': {'OtherAttr': {'StringValue': '5'}}}
    result = dlq_reprocessor.get_reprocess_attempt_count(message)
    assert result == 0


def test_get_reprocess_attempt_count_returns_value_from_attribute(dlq_reprocessor):
    """Test get reprocess attempt count returns value from attribute."""
    message = {
        'MessageAttributes': {
            'ReprocessAttempts': {'DataType': 'Number', 'StringValue': '3'}
        }
    }
    result = dlq_reprocessor.get_reprocess_attempt_count(message)
    assert result == 3


def test_get_reprocess_attempt_count_returns_zero_for_invalid_value(dlq_reprocessor):
    """Test get reprocess attempt count returns zero for invalid value."""
    message = {
        'MessageAttributes': {
            'ReprocessAttempts': {'DataType': 'Number', 'StringValue': 'invalid'}
        }
    }
    result = dlq_reprocessor.get_reprocess_attempt_count(message)
    assert result == 0


def test_reprocess_dlq_messages_returns_dict_with_reprocessed_key(dlq_reprocessor):
    """Test reprocess dlq messages returns dict with reprocessed key."""
    mock_sqs = _create_sqs_with_empty_response(dlq_reprocessor)
    result = _run_reprocess_empty(dlq_reprocessor, mock_sqs)
    assert 'reprocessed' in result


def test_reprocess_dlq_messages_returns_dict_with_skipped_completed_key(dlq_reprocessor):
    """Test reprocess dlq messages returns dict with skipped completed key."""
    mock_sqs = _create_sqs_with_empty_response(dlq_reprocessor)
    result = _run_reprocess_empty(dlq_reprocessor, mock_sqs)
    assert 'skipped_completed' in result


def test_reprocess_dlq_messages_returns_dict_with_skipped_max_retries_key(dlq_reprocessor):
    """Test reprocess dlq messages returns dict with skipped max retries key."""
    mock_sqs = _create_sqs_with_empty_response(dlq_reprocessor)
    result = _run_reprocess_empty(dlq_reprocessor, mock_sqs)
    assert 'skipped_max_retries' in result


def test_reprocess_dlq_messages_returns_dict_with_failed_key(dlq_reprocessor):
    """Test reprocess dlq messages returns dict with failed key."""
    mock_sqs = _create_sqs_with_empty_response(dlq_reprocessor)
    result = _run_reprocess_empty(dlq_reprocessor, mock_sqs)
    assert 'failed' in result


def test_reprocess_dlq_messages_increments_failed_for_invalid_json(dlq_reprocessor):
    """Test reprocess dlq messages increments failed for invalid json."""
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
    """Test reprocess dlq messages skips message exceeding max attempts."""
    attrs = {'ReprocessAttempts': {'DataType': 'Number', 'StringValue': '3'}}
    mock_sqs = _create_sqs_with_message(dlq_reprocessor, 123, attrs)
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value=''):
            with patch.object(dlq_reprocessor, 'send_poison_pill_alert'):
                result = dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
                assert result['skipped_max_retries'] == 1


def test_reprocess_dlq_messages_sends_alert_for_max_retries(dlq_reprocessor):
    """Test reprocess dlq messages sends alert for max retries."""
    attrs = {'ReprocessAttempts': {'DataType': 'Number', 'StringValue': '3'}}
    mock_sqs = _create_sqs_with_message(dlq_reprocessor, 123, attrs)
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value=''):
            with patch.object(dlq_reprocessor, 'send_poison_pill_alert') as mock_alert:
                dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
                assert mock_alert.called


def test_reprocess_dlq_messages_deletes_completed_jobs(dlq_reprocessor):
    """Test reprocess dlq messages deletes completed jobs."""
    mock_sqs = _create_sqs_with_message(dlq_reprocessor, 123)
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value='test-token'):
            with patch.object(dlq_reprocessor, 'check_github_job_status', return_value='completed'):
                result = dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
                assert result['skipped_completed'] == 1


def test_reprocess_dlq_messages_deletes_not_found_jobs(dlq_reprocessor):
    """Test reprocess dlq messages deletes not found jobs."""
    mock_sqs = _create_sqs_with_message(dlq_reprocessor, 456)
    with patch.object(dlq_reprocessor, 'get_sqs_client', return_value=mock_sqs):
        with patch.object(dlq_reprocessor, 'get_github_token', return_value='test-token'):
            with patch.object(dlq_reprocessor, 'check_github_job_status', return_value='not_found'):
                result = dlq_reprocessor.reprocess_dlq_messages('dlq-url', 'target-url')
                assert result['skipped_completed'] == 1


def test_reprocess_dlq_messages_reprocesses_queued_jobs(dlq_reprocessor):
    """Test reprocess dlq messages reprocesses queued jobs."""
    mock_sqs = _create_sqs_with_message(dlq_reprocessor, 789)
    result, _ = _run_reprocess_with_job_status(dlq_reprocessor, mock_sqs, 'queued')
    assert result['reprocessed'] == 1


def test_reprocess_dlq_messages_adds_reprocess_attempts_attribute(dlq_reprocessor):
    """Test reprocess dlq messages adds reprocess attempts attribute."""
    mock_sqs = _create_sqs_with_message(dlq_reprocessor, 111)
    _, sqs = _run_reprocess_with_job_status(dlq_reprocessor, mock_sqs, 'queued')
    call_kwargs = sqs.send_message.call_args[1]
    assert call_kwargs['MessageAttributes']['ReprocessAttempts']['StringValue'] == '1'


def test_reprocess_dlq_messages_increments_existing_reprocess_attempts(dlq_reprocessor):
    """Test reprocess dlq messages increments existing reprocess attempts."""
    attrs = {'ReprocessAttempts': {'DataType': 'Number', 'StringValue': '2'}}
    mock_sqs = _create_sqs_with_message(dlq_reprocessor, 222, attrs)
    _, sqs = _run_reprocess_with_job_status(dlq_reprocessor, mock_sqs, 'queued')
    call_kwargs = sqs.send_message.call_args[1]
    assert call_kwargs['MessageAttributes']['ReprocessAttempts']['StringValue'] == '3'


def test_reprocess_dlq_messages_returns_error_on_receive_failure(dlq_reprocessor):
    """Test reprocess dlq messages returns error on receive failure."""
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
    """Test reprocess dlq messages handles send message failure."""
    mock_sqs = _create_sqs_with_message(dlq_reprocessor, 333)
    mock_sqs.send_message.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Error'}},
        'SendMessage'
    )
    result, _ = _run_reprocess_with_job_status(dlq_reprocessor, mock_sqs, 'queued')
    assert result['failed'] == 1


def test_handler_returns_200_status_code(dlq_reprocessor, lambda_context):
    """Test handler returns 200 status code."""
    env_vars = _create_handler_test_env()
    result = _run_handler_with_empty_sqs(dlq_reprocessor, env_vars, lambda_context)
    assert result['statusCode'] == 200


def test_handler_returns_json_body(dlq_reprocessor, lambda_context):
    """Test handler returns json body."""
    env_vars = _create_handler_test_env()
    result = _run_handler_with_empty_sqs(dlq_reprocessor, env_vars, lambda_context)
    body = json.loads(result['body'])
    assert 'job_dlq' in body


def test_handler_includes_webhook_dlq_note_when_configured(dlq_reprocessor, lambda_context):
    """Test handler includes webhook dlq note when configured."""
    env = {**_create_handler_test_env(), 'WEBHOOK_DLQ_URL': 'webhook-dlq'}
    result = _run_handler_with_empty_sqs(dlq_reprocessor, env, lambda_context)
    body = json.loads(result['body'])
    assert 'webhook_dlq' in body
