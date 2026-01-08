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


class TestHandleSqsEvent:
    """Tests for _handle_sqs_event function."""

    def test_handles_single_valid_record(self, ec2_runner_handler):
        """Test processes single valid SQS record."""
        event = {
            'Records': [{
                'messageId': 'msg-123',
                'body': json.dumps({
                    'job_id': 123,
                    'job_labels': ['ec2', 'test'],
                    'github_repo': 'test/repo',
                    'run_id': 456,
                    'runner_type': 'ec2'
                })
            }]
        }
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            mock_launch.return_value = {'success': True, 'instance_id': 'i-test'}
            result = ec2_runner_handler._handle_sqs_event(event)
            assert result['statusCode'] == 200
            mock_launch.assert_called_once_with(123, ['ec2', 'test'], 'test/repo', 456, 'ec2')

    def test_handles_multiple_valid_records(self, ec2_runner_handler):
        """Test processes multiple SQS records."""
        event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'job_id': 1,
                        'job_labels': ['ec2'],
                        'github_repo': 'test/repo1'
                    })
                },
                {
                    'messageId': 'msg-2',
                    'body': json.dumps({
                        'job_id': 2,
                        'job_labels': ['ec2'],
                        'github_repo': 'test/repo2'
                    })
                }
            ]
        }
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            mock_launch.return_value = {'success': True, 'instance_id': 'i-test'}
            result = ec2_runner_handler._handle_sqs_event(event)
            assert result['statusCode'] == 200
            assert mock_launch.call_count == 2

    def test_handles_missing_job_id(self, ec2_runner_handler):
        """Test handles record with missing job_id."""
        event = {
            'Records': [{
                'messageId': 'msg-123',
                'body': json.dumps({
                    'job_labels': ['ec2'],
                    'github_repo': 'test/repo'
                })
            }]
        }
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            result = ec2_runner_handler._handle_sqs_event(event)
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert body['results'][0]['error'] == 'Missing required fields'
            mock_launch.assert_not_called()

    def test_handles_missing_github_repo(self, ec2_runner_handler):
        """Test handles record with missing github_repo."""
        event = {
            'Records': [{
                'messageId': 'msg-123',
                'body': json.dumps({
                    'job_id': 123,
                    'job_labels': ['ec2']
                })
            }]
        }
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            result = ec2_runner_handler._handle_sqs_event(event)
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert body['results'][0]['error'] == 'Missing required fields'
            mock_launch.assert_not_called()

    def test_handles_invalid_json_body(self, ec2_runner_handler):
        """Test handles record with invalid JSON body."""
        event = {
            'Records': [{
                'messageId': 'msg-123',
                'body': 'not-valid-json'
            }]
        }
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            result = ec2_runner_handler._handle_sqs_event(event)
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert 'error' in body['results'][0]
            mock_launch.assert_not_called()

    def test_handles_launch_failure(self, ec2_runner_handler):
        """Test handles EC2 launch failure gracefully."""
        event = {
            'Records': [{
                'messageId': 'msg-123',
                'body': json.dumps({
                    'job_id': 123,
                    'job_labels': ['ec2'],
                    'github_repo': 'test/repo'
                })
            }]
        }
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            mock_launch.return_value = {'success': False, 'error': 'No capacity'}
            result = ec2_runner_handler._handle_sqs_event(event)
            # Should still return 200 - SQS message processed
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert body['results'][0]['result']['success'] is False

    def test_uses_default_runner_type(self, ec2_runner_handler):
        """Test uses default runner_type when not specified."""
        event = {
            'Records': [{
                'messageId': 'msg-123',
                'body': json.dumps({
                    'job_id': 123,
                    'job_labels': ['ec2'],
                    'github_repo': 'test/repo'
                })
            }]
        }
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            mock_launch.return_value = {'success': True}
            ec2_runner_handler._handle_sqs_event(event)
            # Default runner_type should be 'ec2'
            call_args = mock_launch.call_args
            assert call_args[0][4] == 'ec2'  # runner_type argument


class TestLambdaHandlerSqsDispatch:
    """Tests for SQS event dispatch in lambda_handler."""

    def test_dispatches_sqs_event(self, ec2_runner_handler, lambda_context):
        """Test dispatches to SQS handler when event has SQS records."""
        event = {
            'Records': [{
                'eventSource': 'aws:sqs',
                'messageId': 'msg-123',
                'body': json.dumps({
                    'job_id': 123,
                    'job_labels': ['ec2'],
                    'github_repo': 'test/repo'
                })
            }]
        }
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


class TestHandlerPostException:
    """Tests for exception handling in POST handler."""

    def test_post_handler_catches_value_error(self, ec2_runner_handler, lambda_context):
        """Test POST handler catches ValueError and returns 500."""
        event = {
            'path': '/v1/runners/ec2',
            'httpMethod': 'POST',
            'headers': {},
            'body': json.dumps({'job_id': 123, 'github_repo': 'test/repo'})
        }
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            mock_launch.side_effect = ValueError('Test error')
            response = ec2_runner_handler.lambda_handler(event, lambda_context)
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert body['success'] is False
            assert 'error' in body

    def test_post_handler_catches_key_error(self, ec2_runner_handler, lambda_context):
        """Test POST handler catches KeyError and returns 500."""
        event = {
            'path': '/v1/runners/ec2',
            'httpMethod': 'POST',
            'headers': {},
            'body': json.dumps({'job_id': 123, 'github_repo': 'test/repo'})
        }
        with patch.object(ec2_runner_handler, 'launch_ec2_runner') as mock_launch:
            mock_launch.side_effect = KeyError('missing_key')
            response = ec2_runner_handler.lambda_handler(event, lambda_context)
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert body['success'] is False
