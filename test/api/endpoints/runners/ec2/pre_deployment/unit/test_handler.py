"""Unit tests for EC2 runner Lambda handler."""
import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from botocore.exceptions import ClientError

from .conftest import (
    assert_json_content_type,
    assert_response_status,
    create_mock_ec2_with_ami,
    create_multi_client_mock,
    get_minimal_env_vars,
    parse_response_body,
)


# =============================================================================
# Fixtures for SQS event construction (reduces duplication)
# =============================================================================


@pytest.fixture
def sqs_record_factory():
    """Factory for creating SQS record dicts."""
    def _create(message_id='msg-123', job_id=123, job_labels=None,
                github_repo='test/repo', run_id=None, runner_type=None,
                raw_body=None):
        if raw_body is not None:
            return {'messageId': message_id, 'body': raw_body}
        body = {}
        if job_id is not None:
            body['job_id'] = job_id
        if job_labels is not None:
            body['job_labels'] = job_labels
        else:
            body['job_labels'] = ['ec2', 'test']
        if github_repo is not None:
            body['github_repo'] = github_repo
        if run_id is not None:
            body['run_id'] = run_id
        if runner_type is not None:
            body['runner_type'] = runner_type
        return {'messageId': message_id, 'body': json.dumps(body)}
    return _create


@pytest.fixture
def sqs_event_factory(sqs_record_factory):
    """Factory for creating SQS events with records."""
    def _create(records=None, **kwargs):
        if records is not None:
            return {'Records': records}
        return {'Records': [sqs_record_factory(**kwargs)]}
    return _create


@pytest.fixture
def post_error_event():
    """Event for testing POST error handling."""
    return {
        'path': '/v1/runners/ec2',
        'httpMethod': 'POST',
        'headers': {},
        'body': json.dumps({'job_id': 123, 'github_repo': 'test/repo'})
    }


# =============================================================================
# POST Request Tests
# =============================================================================


def test_lambda_handler_ec2_runner_post_with_missing_job_id_returns_400(
    ec2_runner_handler, ec2_runner_post_event_factory, lambda_context
):
    """Test that POST without job_id returns 400."""
    event = ec2_runner_post_event_factory()
    body = json.loads(event['body'])
    del body['job_id']
    event['body'] = json.dumps(body)
    response = ec2_runner_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_lambda_handler_ec2_runner_post_with_missing_repo_returns_400(
    ec2_runner_handler, ec2_runner_post_event_factory, lambda_context
):
    """Test that POST without github_repo returns 400."""
    event = ec2_runner_post_event_factory()
    body = json.loads(event['body'])
    del body['github_repo']
    event['body'] = json.dumps(body)
    response = ec2_runner_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 400


@pytest.mark.usefixtures('mock_boto_client')
def test_lambda_handler_ec2_runner_post_returns_json_content_type(
    ec2_runner_handler, ec2_runner_post_event_factory, lambda_context
):
    """Test that POST returns JSON content type."""
    event = ec2_runner_post_event_factory(job_id=12345, github_repo='test-org/test-repo')
    response = ec2_runner_handler.lambda_handler(event, lambda_context)
    assert response['headers']['Content-Type'].startswith('application/json')


# =============================================================================
# GET Status Tests
# =============================================================================


def test_get_ec2_runner_status_returns_success_with_no_instances(ec2_runner_handler):
    """Test that status returns success with no instances."""
    with patch('fleet_ops.get_ec2_client') as mock_get_client:
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {'Reservations': []}
        mock_get_client.return_value = mock_ec2
        result = ec2_runner_handler.get_ec2_runner_status()
        is_success = result['success']
        assert is_success


def test_get_ec2_runner_status_returns_zero_running_instances_when_empty(ec2_runner_handler):
    """Test that status returns zero running instances when empty."""
    with patch('fleet_ops.get_ec2_client') as mock_get_client:
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {'Reservations': []}
        mock_get_client.return_value = mock_ec2
        result = ec2_runner_handler.get_ec2_runner_status()
        has_zero_instances = result['running_instances'] == 0
        assert has_zero_instances


def test_get_ec2_runner_status_returns_empty_instance_list_when_none_running(ec2_runner_handler):
    """Test that status returns empty instance list when none running."""
    with patch('fleet_ops.get_ec2_client') as mock_get_client:
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {'Reservations': []}
        mock_get_client.return_value = mock_ec2
        result = ec2_runner_handler.get_ec2_runner_status()
        is_empty_list = result['instances'] == []
        assert is_empty_list


def test_get_ec2_runner_status_handles_client_error(ec2_runner_handler):
    """Test that status handles client errors gracefully."""
    with patch('fleet_ops.get_ec2_client') as mock_get_client:
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.side_effect = ClientError(
            {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
            'describe_instances'
        )
        mock_get_client.return_value = mock_ec2
        result = ec2_runner_handler.get_ec2_runner_status()
        is_failure = not result['success']
        assert is_failure


def test_get_ec2_runner_status_filters_by_managed_by_tag_from_env(ec2_runner_handler):
    """Test that status filters by ManagedBy tag."""
    with patch('fleet_ops.get_ec2_client') as mock_get_client:
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {'Reservations': []}
        mock_get_client.return_value = mock_ec2
        ec2_runner_handler.get_ec2_runner_status()
        call_args = mock_ec2.describe_instances.call_args
        filters = call_args[1]['Filters']
        managed_by_filter = next(f for f in filters if f['Name'] == 'tag:ManagedBy')
        has_correct_tag = managed_by_filter['Values'] == ['api-ec2-runner']
        assert has_correct_tag


def test_handle_ec2_runner_get_returns_200_status(
    ec2_runner_handler, ec2_runner_get_event, lambda_context
):
    """Test that GET handler returns 200 status."""
    with patch.object(ec2_runner_handler, 'get_ec2_runner_status') as mock_status:
        mock_status.return_value = {'success': True, 'running_instances': 0, 'instances': []}
        response = ec2_runner_handler.lambda_handler(ec2_runner_get_event, lambda_context)
        assert response['statusCode'] == 200


def test_handle_ec2_runner_get_returns_json_content_type(
    ec2_runner_handler, ec2_runner_get_event, lambda_context
):
    """Test that GET handler returns JSON content type."""
    with patch.object(ec2_runner_handler, 'get_ec2_runner_status') as mock_status:
        mock_status.return_value = {'success': True, 'running_instances': 0, 'instances': []}
        response = ec2_runner_handler.lambda_handler(ec2_runner_get_event, lambda_context)
        assert response['headers']['Content-Type'].startswith('application/json')


# =============================================================================
# Launch EC2 Runner Tests
# =============================================================================


@patch('boto3.client')
def test_launch_ec2_runner_no_ami(mock_boto_client, ec2_runner_handler):
    """Test that launch fails gracefully when no AMI is available."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_images.return_value = {'Images': []}
    mock_boto_client.return_value = mock_ec2
    with patch.dict('os.environ', {
        'SUBNETS': 'subnet-1',
        'SECURITY_GROUPS': 'sg-1',
        'EC2_INSTANCE_TYPES': 't3.small',
        'EC2_IAM_INSTANCE_PROFILE': 'profile',
        'API_FQDN': 'api.test.com'
    }):
        with patch('fleet_ops.trigger_ami_creation', return_value={'success': True}):
            result = ec2_runner_handler.launch_ec2_runner(123, ['test'], 'test/repo')
            is_failure = not result['success']
            assert is_failure


@patch('boto3.client')
def test_launch_ec2_runner_insufficient_capacity_all_azs(mock_boto_client, ec2_runner_handler):
    """Test that launch fails when all AZs have insufficient capacity."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_images.return_value = {
        'Images': [{'ImageId': 'ami-test', 'CreationDate': '2024-01-01T00:00:00'}]
    }
    mock_ec2.create_launch_template.return_value = {
        'LaunchTemplate': {'LaunchTemplateId': 'lt-12345'}
    }
    mock_ec2.create_fleet.return_value = {
        'Instances': [],
        'Errors': [{'ErrorCode': 'InsufficientInstanceCapacity', 'ErrorMessage': 'No capacity'}]
    }
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}

    mock_boto_client.side_effect = create_multi_client_mock(mock_ec2, mock_ssm)

    with patch.dict('os.environ', {
        'SUBNETS': 'subnet-1,subnet-2',
        'SECURITY_GROUPS': 'sg-1',
        'EC2_INSTANCE_TYPES': 't3.small',
        'EC2_IAM_INSTANCE_PROFILE': 'profile',
        'GITHUB_TOKEN_SECRET_NAME': '/token'
    }):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps({'token': 'reg-token'}).encode()
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response
            result = ec2_runner_handler.launch_ec2_runner(123, ['test'], 'test/repo')
            is_failure = not result['success']
            assert is_failure


@patch('boto3.client')
def test_launch_ec2_runner_no_github_token(mock_boto_client, ec2_runner_handler):
    """Test that launch fails when GitHub token is not available."""
    mock_boto_client.return_value = create_mock_ec2_with_ami()
    with patch.dict('os.environ', get_minimal_env_vars()):
        with patch('fleet_ops.get_github_token', return_value=''):
            result = ec2_runner_handler.launch_ec2_runner(123, ['test'], 'test/repo')
            is_failure = not result['success']
            assert is_failure


@patch('boto3.client')
def test_launch_ec2_runner_failed_registration(mock_boto_client, ec2_runner_handler):
    """Test that launch fails when runner registration fails."""
    mock_boto_client.return_value = create_mock_ec2_with_ami()
    with patch.dict('os.environ', get_minimal_env_vars()):
        with patch('fleet_ops.get_github_token', return_value='token'):
            with patch('fleet_ops.get_runner_registration_token', return_value=''):
                result = ec2_runner_handler.launch_ec2_runner(123, ['test'], 'test/repo')
                is_failure = not result['success']
                assert is_failure


# =============================================================================
# HTTP Method Tests
# =============================================================================


def test_lambda_handler_options_returns_200(ec2_runner_handler, lambda_context):
    """Test that OPTIONS request returns 200."""
    event = {'path': '/v1/runners/ec2', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = ec2_runner_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 200


def test_lambda_handler_unknown_path_returns_404(ec2_runner_handler, lambda_context):
    """Test that unknown path returns 404."""
    event = {'path': '/v1/unknown', 'httpMethod': 'GET', 'headers': {}}
    response = ec2_runner_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 404


# =============================================================================
# Test Mode Tests
# =============================================================================


def test_test_mode_header_sets_test_mode(ec2_runner_handler, lambda_context):
    """Test that x-test-mode header enables test mode."""
    event = {
        'path': '/v1/runners/ec2',
        'httpMethod': 'GET',
        'headers': {'x-test-mode': 'true'}
    }
    with patch.object(ec2_runner_handler, 'get_ec2_runner_status') as mock_status:
        mock_status.return_value = {'success': True, 'running_instances': 0, 'instances': []}
        ec2_runner_handler.lambda_handler(event, lambda_context)
        is_test_mode = ec2_runner_handler.is_test_mode()
        assert is_test_mode


def test_test_mode_post_returns_mock_response(
    ec2_runner_handler, ec2_runner_post_event_factory, lambda_context
):
    """Test that test mode POST returns mock response."""
    event = ec2_runner_post_event_factory(job_id=123, github_repo='test/repo')
    event['headers'] = {'x-test-mode': 'true'}
    response = ec2_runner_handler.lambda_handler(event, lambda_context)
    body = parse_response_body(response)
    is_test_mode = body.get('test_mode')
    assert is_test_mode


# =============================================================================
# get_header_case_insensitive Tests
# =============================================================================


class TestGetHeaderCaseInsensitive:
    """Tests for get_header_case_insensitive function."""

    def test_returns_header_value_lowercase(self, ec2_runner_handler):
        """Test returns header value when key is lowercase."""
        result = ec2_runner_handler.get_header_case_insensitive(
            {'x-api-key': 'test-value'}, 'x-api-key'
        )
        assert result == 'test-value'

    def test_returns_header_value_mixed_case(self, ec2_runner_handler):
        """Test returns header value when key case differs."""
        result = ec2_runner_handler.get_header_case_insensitive(
            {'X-Api-Key': 'test-value'}, 'x-api-key'
        )
        assert result == 'test-value'

    def test_returns_empty_string_when_not_found(self, ec2_runner_handler):
        """Test returns empty string when header not found."""
        result = ec2_runner_handler.get_header_case_insensitive(
            {'other-header': 'value'}, 'x-api-key'
        )
        assert result == ''

    def test_returns_empty_string_when_headers_none(self, ec2_runner_handler):
        """Test returns empty string when headers is None."""
        result = ec2_runner_handler.get_header_case_insensitive(None, 'x-api-key')
        assert result == ''

    def test_returns_empty_string_when_headers_empty(self, ec2_runner_handler):
        """Test returns empty string when headers is empty dict."""
        result = ec2_runner_handler.get_header_case_insensitive({}, 'x-api-key')
        assert result == ''

    def test_returns_empty_string_when_value_is_none(self, ec2_runner_handler):
        """Test returns empty string when header value is None."""
        result = ec2_runner_handler.get_header_case_insensitive(
            {'x-api-key': None}, 'x-api-key'
        )
        assert result == ''


# =============================================================================
# SQS Event Handling Tests
# =============================================================================


class TestHandleSqsEventSingleRecord:
    """Tests for _handle_sqs_event with single valid record."""

    def test_returns_200_status(self, ec2_runner_handler, sqs_event_factory):
        """Test single valid record returns 200."""
        event = sqs_event_factory(run_id=456, runner_type='ec2')
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            mock_launch.return_value = {'success': True, 'instance_id': 'i-test'}
            result = ec2_runner_handler._handle_sqs_event(event)
            assert result['statusCode'] == 200

    def test_calls_launch_with_correct_args(self, ec2_runner_handler, sqs_event_factory):
        """Test single valid record calls launch with correct arguments."""
        event = sqs_event_factory(run_id=456, runner_type='ec2')
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            mock_launch.return_value = {'success': True, 'instance_id': 'i-test'}
            ec2_runner_handler._handle_sqs_event(event)
            mock_launch.assert_called_once_with(123, ['ec2', 'test'], 'test/repo', 456, 'ec2')


class TestHandleSqsEventMultipleRecords:
    """Tests for _handle_sqs_event with multiple records."""

    @pytest.fixture
    def multi_record_event(self, sqs_record_factory):
        """Event with multiple SQS records."""
        return {
            'Records': [
                sqs_record_factory(message_id='msg-1', job_id=1, github_repo='test/repo1'),
                sqs_record_factory(message_id='msg-2', job_id=2, github_repo='test/repo2'),
            ]
        }

    def test_returns_200_status(self, ec2_runner_handler, multi_record_event):
        """Test multiple records returns 200."""
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            mock_launch.return_value = {'success': True, 'instance_id': 'i-test'}
            result = ec2_runner_handler._handle_sqs_event(multi_record_event)
            assert result['statusCode'] == 200

    def test_processes_all_records(self, ec2_runner_handler, multi_record_event):
        """Test all records are processed."""
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            mock_launch.return_value = {'success': True, 'instance_id': 'i-test'}
            ec2_runner_handler._handle_sqs_event(multi_record_event)
            assert mock_launch.call_count == 2


class TestHandleSqsEventMissingJobId:
    """Tests for _handle_sqs_event with missing job_id."""

    @pytest.fixture
    def missing_job_id_event(self, sqs_event_factory):
        """Event with missing job_id."""
        return sqs_event_factory(job_id=None)

    def test_returns_200_status(self, ec2_runner_handler, missing_job_id_event):
        """Test missing job_id still returns 200 (message processed)."""
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            result = ec2_runner_handler._handle_sqs_event(missing_job_id_event)
            assert result['statusCode'] == 200

    def test_returns_error_in_results(self, ec2_runner_handler, missing_job_id_event):
        """Test missing job_id returns error in results."""
        with patch.object(ec2_runner_handler, 'launch_ec2_runner'):
            result = ec2_runner_handler._handle_sqs_event(missing_job_id_event)
            body = json.loads(result['body'])
            assert body['results'][0]['error'] == 'Missing required fields'

    def test_does_not_call_launch(self, ec2_runner_handler, missing_job_id_event):
        """Test missing job_id does not call launch."""
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            ec2_runner_handler._handle_sqs_event(missing_job_id_event)
            mock_launch.assert_not_called()


class TestHandleSqsEventMissingGithubRepo:
    """Tests for _handle_sqs_event with missing github_repo."""

    @pytest.fixture
    def missing_repo_event(self, sqs_event_factory):
        """Event with missing github_repo."""
        return sqs_event_factory(github_repo=None)

    def test_returns_200_status(self, ec2_runner_handler, missing_repo_event):
        """Test missing github_repo still returns 200."""
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            result = ec2_runner_handler._handle_sqs_event(missing_repo_event)
            assert result['statusCode'] == 200

    def test_returns_error_in_results(self, ec2_runner_handler, missing_repo_event):
        """Test missing github_repo returns error in results."""
        with patch.object(ec2_runner_handler, 'launch_ec2_runner'):
            result = ec2_runner_handler._handle_sqs_event(missing_repo_event)
            body = json.loads(result['body'])
            assert body['results'][0]['error'] == 'Missing required fields'

    def test_does_not_call_launch(self, ec2_runner_handler, missing_repo_event):
        """Test missing github_repo does not call launch."""
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            ec2_runner_handler._handle_sqs_event(missing_repo_event)
            mock_launch.assert_not_called()


class TestHandleSqsEventInvalidJson:
    """Tests for _handle_sqs_event with invalid JSON body."""

    @pytest.fixture
    def invalid_json_event(self, sqs_event_factory):
        """Event with invalid JSON body."""
        return sqs_event_factory(raw_body='not-valid-json')

    def test_returns_200_status(self, ec2_runner_handler, invalid_json_event):
        """Test invalid JSON still returns 200."""
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            result = ec2_runner_handler._handle_sqs_event(invalid_json_event)
            assert result['statusCode'] == 200

    def test_returns_error_in_results(self, ec2_runner_handler, invalid_json_event):
        """Test invalid JSON returns error in results."""
        with patch.object(ec2_runner_handler, 'launch_ec2_runner'):
            result = ec2_runner_handler._handle_sqs_event(invalid_json_event)
            body = json.loads(result['body'])
            assert 'error' in body['results'][0]

    def test_does_not_call_launch(self, ec2_runner_handler, invalid_json_event):
        """Test invalid JSON does not call launch."""
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            ec2_runner_handler._handle_sqs_event(invalid_json_event)
            mock_launch.assert_not_called()


class TestHandleSqsEventLaunchFailure:
    """Tests for _handle_sqs_event when launch fails."""

    @pytest.fixture
    def launch_failure_result(self, ec2_runner_handler, sqs_event_factory):
        """Execute SQS handler with launch failure and return result."""
        event = sqs_event_factory()
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            mock_launch.return_value = {'success': False, 'error': 'No capacity'}
            return ec2_runner_handler._handle_sqs_event(event)

    def test_returns_200_status(self, launch_failure_result):
        """Test launch failure still returns 200 (message processed)."""
        assert launch_failure_result['statusCode'] == 200

    def test_returns_failure_in_results(self, launch_failure_result):
        """Test launch failure returns success=False in results."""
        body = json.loads(launch_failure_result['body'])
        assert body['results'][0]['result']['success'] is False


class TestHandleSqsEventDefaultRunnerType:
    """Tests for _handle_sqs_event default runner_type."""

    def test_uses_default_runner_type(self, ec2_runner_handler, sqs_event_factory):
        """Test uses default runner_type when not specified."""
        event = sqs_event_factory()
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            mock_launch.return_value = {'success': True}
            ec2_runner_handler._handle_sqs_event(event)
            call_args = mock_launch.call_args
            assert call_args[0][4] == 'ec2'


# =============================================================================
# SQS Event Dispatch Tests
# =============================================================================


class TestLambdaHandlerSqsDispatch:
    """Tests for SQS event dispatch in lambda_handler."""

    def test_dispatches_sqs_event(self, ec2_runner_handler, lambda_context, sqs_event_factory):
        """Test dispatches to SQS handler when event has SQS records."""
        event = sqs_event_factory()
        event['Records'][0]['eventSource'] = 'aws:sqs'
        with patch.object(ec2_runner_handler, '_handle_sqs_event') as mock_sqs:
            mock_sqs.return_value = {'statusCode': 200, 'body': '{}'}
            ec2_runner_handler.lambda_handler(event, lambda_context)
            mock_sqs.assert_called_once_with(event)

    def test_does_not_dispatch_http_event_as_sqs(self, ec2_runner_handler, lambda_context):
        """Test does not dispatch HTTP event to SQS handler."""
        event = {
            'path': '/v1/runners/ec2',
            'httpMethod': 'GET',
            'headers': {}
        }
        with patch.object(ec2_runner_handler, '_handle_sqs_event') as mock_sqs:
            with patch.object(ec2_runner_handler, 'get_ec2_runner_status') as mock_status:
                mock_status.return_value = {'success': True, 'running_instances': 0, 'instances': []}
                ec2_runner_handler.lambda_handler(event, lambda_context)
                mock_sqs.assert_not_called()


# =============================================================================
# POST Exception Handling Tests
# =============================================================================


class TestHandlerPostValueError:
    """Tests for ValueError handling in POST handler."""

    @pytest.fixture
    def value_error_response(self, ec2_runner_handler, lambda_context, post_error_event):
        """Execute POST handler with ValueError and return response."""
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            mock_launch.side_effect = ValueError('Test error')
            return ec2_runner_handler.lambda_handler(post_error_event, lambda_context)

    def test_returns_500_status(self, value_error_response):
        """Test ValueError returns 500 status."""
        assert value_error_response['statusCode'] == 500

    def test_returns_success_false(self, value_error_response):
        """Test ValueError returns success=False."""
        body = json.loads(value_error_response['body'])
        assert body['success'] is False

    def test_returns_error_message(self, value_error_response):
        """Test ValueError returns error in body."""
        body = json.loads(value_error_response['body'])
        assert 'error' in body


class TestHandlerPostKeyError:
    """Tests for KeyError handling in POST handler."""

    @pytest.fixture
    def key_error_response(self, ec2_runner_handler, lambda_context, post_error_event):
        """Execute POST handler with KeyError and return response."""
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            mock_launch.side_effect = KeyError('missing_key')
            return ec2_runner_handler.lambda_handler(post_error_event, lambda_context)

    def test_returns_500_status(self, key_error_response):
        """Test KeyError returns 500 status."""
        assert key_error_response['statusCode'] == 500

    def test_returns_success_false(self, key_error_response):
        """Test KeyError returns success=False."""
        body = json.loads(key_error_response['body'])
        assert body['success'] is False
