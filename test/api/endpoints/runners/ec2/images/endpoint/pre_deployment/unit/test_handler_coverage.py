"""Unit tests to improve handler.py coverage.

These tests cover previously untested code paths in handler.py.
"""
from unittest.mock import MagicMock, patch
import pytest
from botocore.exceptions import ClientError


class TestTestModeHelpers:
    """Tests for test mode helper functions."""

    def test_is_test_mode_returns_false_by_default(self, handler_module):
        """Verify is_test_mode returns False by default."""
        handler_module._test_mode['enabled'] = False
        assert handler_module.is_test_mode() is False

    def test_is_test_mode_returns_true_when_enabled(self, handler_module):
        """Verify is_test_mode returns True when enabled."""
        handler_module._test_mode['enabled'] = True
        assert handler_module.is_test_mode() is True

    def test_set_test_mode_enables_test_mode(self, handler_module):
        """Verify set_test_mode enables test mode."""
        handler_module.set_test_mode(True)
        assert handler_module._test_mode['enabled'] is True

    def test_set_test_mode_disables_test_mode(self, handler_module):
        """Verify set_test_mode disables test mode."""
        handler_module._test_mode['enabled'] = True
        handler_module.set_test_mode(False)
        assert handler_module._test_mode['enabled'] is False


class TestGetHeaderCaseInsensitive:
    """Tests for get_header_case_insensitive function."""

    def test_returns_empty_string_for_none_headers(self, handler_module):
        """Verify returns empty string when headers is None."""
        result = handler_module.get_header_case_insensitive(None, 'Content-Type')
        assert result == ''

    def test_returns_empty_string_for_empty_headers(self, handler_module):
        """Verify returns empty string when headers is empty."""
        result = handler_module.get_header_case_insensitive({}, 'Content-Type')
        assert result == ''

    def test_finds_header_with_exact_case(self, handler_module):
        """Verify finds header with exact case match."""
        headers = {'Content-Type': 'application/json'}
        result = handler_module.get_header_case_insensitive(headers, 'Content-Type')
        assert result == 'application/json'

    def test_finds_header_case_insensitively(self, handler_module):
        """Verify finds header regardless of case."""
        headers = {'content-type': 'application/json'}
        result = handler_module.get_header_case_insensitive(headers, 'Content-Type')
        assert result == 'application/json'

    def test_returns_empty_string_for_missing_header(self, handler_module):
        """Verify returns empty string when header not found."""
        headers = {'X-Custom': 'value'}
        result = handler_module.get_header_case_insensitive(headers, 'Content-Type')
        assert result == ''

    def test_returns_empty_string_for_none_value(self, handler_module):
        """Verify returns empty string when header value is None."""
        headers = {'Content-Type': None}
        result = handler_module.get_header_case_insensitive(headers, 'Content-Type')
        assert result == ''


def _fetch_token_from_ssm(handler_module):
    """Helper to fetch token from SSM."""
    handler_module._github_token_cache['value'] = ''
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'ssm-token'}}
    with patch.object(handler_module.boto3, 'client', return_value=mock_ssm):
        return handler_module.get_github_token()


class TestGetGithubToken:
    """Tests for get_github_token function."""

    def test_returns_cached_token_if_available(self, handler_module):
        """Verify returns cached token without calling SSM."""
        handler_module._github_token_cache['value'] = 'cached-token'
        result = handler_module.get_github_token()
        assert result == 'cached-token'

    def test_fetches_token_from_ssm_returns_token(self, handler_module):
        """Verify fetches token from SSM returns the token value."""
        result = _fetch_token_from_ssm(handler_module)
        assert result == 'ssm-token'

    def test_fetches_token_from_ssm_updates_cache(self, handler_module):
        """Verify fetches token from SSM updates the cache."""
        _fetch_token_from_ssm(handler_module)
        assert handler_module._github_token_cache['value'] == 'ssm-token'

    def test_returns_empty_string_on_ssm_error(self, handler_module):
        """Verify returns empty string on SSM client error."""
        handler_module._github_token_cache['value'] = ''
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'GetParameter'
        )
        with patch.object(handler_module.boto3, 'client', return_value=mock_ssm):
            result = handler_module.get_github_token()
        assert result == ''


def _make_mock_http_response(status: int) -> MagicMock:
    """Create a mock HTTP response with context manager support."""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


def _trigger_workflow_without_token(handler_module):
    """Helper to trigger workflow when no token is available."""
    handler_module._github_token_cache['value'] = ''
    with patch.object(handler_module.boto3, 'client') as mock_client:
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'GetParameter'
        )
        mock_client.return_value = mock_ssm
        return handler_module.trigger_github_workflow('test.yml', {'ref': 'main'})


def _trigger_workflow_with_response(handler_module, status: int):
    """Helper to trigger workflow with a mock HTTP response."""
    handler_module._github_token_cache['value'] = 'test-token'
    mock_response = _make_mock_http_response(status)
    with patch.object(handler_module.urllib.request, 'urlopen', return_value=mock_response):
        return handler_module.trigger_github_workflow('test.yml', {'ref': 'main'})


class TestTriggerGithubWorkflow:
    """Tests for trigger_github_workflow function."""

    def test_returns_failure_when_no_token(self, handler_module):
        """Verify returns success=False when GitHub token is not available."""
        result = _trigger_workflow_without_token(handler_module)
        assert result['success'] is False

    def test_returns_token_error_message_when_no_token(self, handler_module):
        """Verify error mentions GITHUB_TOKEN when token is not available."""
        result = _trigger_workflow_without_token(handler_module)
        assert 'GITHUB_TOKEN' in result['error']

    def test_returns_success_on_204_response(self, handler_module):
        """Verify returns success when GitHub API returns 204."""
        result = _trigger_workflow_with_response(handler_module, 204)
        assert result['success'] is True

    def test_returns_failure_on_non_204_response(self, handler_module):
        """Verify returns success=False when GitHub API returns non-204."""
        result = _trigger_workflow_with_response(handler_module, 500)
        assert result['success'] is False

    def test_returns_status_in_error_on_non_204_response(self, handler_module):
        """Verify error includes status code when GitHub API returns non-204."""
        result = _trigger_workflow_with_response(handler_module, 500)
        assert '500' in result['error']

    def test_returns_error_on_url_error(self, handler_module):
        """Verify returns error on URL error."""
        handler_module._github_token_cache['value'] = 'test-token'
        with patch.object(
            handler_module.urllib.request,
            'urlopen',
            side_effect=handler_module.urllib.error.URLError('Connection failed')
        ):
            result = handler_module.trigger_github_workflow('test.yml', {'ref': 'main'})
        assert result['success'] is False


def _handle_post_in_test_mode(handler_module):
    """Helper to call handle_post_request in test mode."""
    handler_module.set_test_mode(True)
    event = {'path': '/v1/runners/ec2/images'}
    return handler_module.handle_post_request(event, lambda x: x)


class TestHandlePostRequest:
    """Tests for handle_post_request function."""

    def test_returns_200_in_test_mode(self, handler_module):
        """Verify returns 200 status when test mode is enabled."""
        result = _handle_post_in_test_mode(handler_module)
        assert result['statusCode'] == 200

    def test_returns_test_mode_flag_in_body(self, handler_module):
        """Verify response body has test_mode=True when test mode is enabled."""
        result = _handle_post_in_test_mode(handler_module)
        body = handler_module.json.loads(result['body'])
        assert body['test_mode'] is True

    def test_calls_handler_func_when_not_test_mode(self, handler_module):
        """Verify calls handler function when not in test mode."""
        handler_module.set_test_mode(False)
        event = {'path': '/v1/runners/ec2/images', 'body': '{}'}
        mock_handler = MagicMock(return_value={'result': 'success'})
        handler_module.handle_post_request(event, mock_handler)
        mock_handler.assert_called_once()
        assert True  # Explicit pass

    def test_returns_200_when_handler_succeeds(self, handler_module):
        """Verify returns 200 when handler function succeeds."""
        handler_module.set_test_mode(False)
        event = {'path': '/v1/runners/ec2/images', 'body': '{}'}
        mock_handler = MagicMock(return_value={'result': 'success'})
        result = handler_module.handle_post_request(event, mock_handler)
        assert result['statusCode'] == 200

    def test_returns_500_on_exception(self, handler_module):
        """Verify returns 500 error on exception."""
        handler_module.set_test_mode(False)
        event = {'path': '/v1/runners/ec2/images', 'body': '{}'}
        mock_handler = MagicMock(side_effect=ValueError('Test error'))
        result = handler_module.handle_post_request(event, mock_handler)
        assert result['statusCode'] == 500


def _list_amis_with_error(handler_module, mock_ec2):
    """Helper to call list_amis with an EC2 error."""
    mock_ec2.describe_images.side_effect = ClientError(
        {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
        'DescribeImages'
    )
    return handler_module.list_amis()


class TestListAmisErrorHandling:
    """Tests for list_amis error handling."""

    def test_returns_failure_on_client_error(self, handler_module, mock_ec2):
        """Verify returns success=False on EC2 client error."""
        result = _list_amis_with_error(handler_module, mock_ec2)
        assert result['success'] is False

    def test_returns_error_key_on_client_error(self, handler_module, mock_ec2):
        """Verify returns error key on EC2 client error."""
        result = _list_amis_with_error(handler_module, mock_ec2)
        assert 'error' in result


def _get_latest_ami_with_error(handler_module, mock_ec2):
    """Helper to call get_latest_ami_details with an EC2 error."""
    mock_ec2.describe_images.side_effect = ClientError(
        {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
        'DescribeImages'
    )
    return handler_module.get_latest_ami_details()


class TestGetLatestAmiDetailsErrorHandling:
    """Tests for get_latest_ami_details error handling."""

    def test_returns_failure_on_client_error(self, handler_module, mock_ec2):
        """Verify returns success=False on EC2 client error."""
        result = _get_latest_ami_with_error(handler_module, mock_ec2)
        assert result['success'] is False

    def test_returns_error_key_on_client_error(self, handler_module, mock_ec2):
        """Verify returns error key on EC2 client error."""
        result = _get_latest_ami_with_error(handler_module, mock_ec2)
        assert 'error' in result


def _deregister_nonexistent_ami(handler_module, mock_ec2):
    """Helper to deregister a nonexistent AMI."""
    mock_ec2.describe_images.return_value = {'Images': []}
    return handler_module.deregister_ami('ami-nonexistent')


def _setup_ami_with_snapshots(mock_ec2):
    """Setup mock EC2 for AMI with snapshots."""
    mock_ec2.describe_images.return_value = {
        'Images': [{
            'ImageId': 'ami-test',
            'BlockDeviceMappings': [
                {'Ebs': {'SnapshotId': 'snap-123'}},
                {'Ebs': {'SnapshotId': 'snap-456'}}
            ]
        }]
    }
    mock_ec2.deregister_image.return_value = {}
    mock_ec2.delete_snapshot.return_value = {}


class TestDeregisterAmi:
    """Tests for deregister_ami function."""

    def test_returns_failure_when_ami_not_found(self, handler_module, mock_ec2):
        """Verify returns success=False when AMI not found."""
        result = _deregister_nonexistent_ami(handler_module, mock_ec2)
        assert result['success'] is False

    def test_returns_not_found_error_when_ami_not_found(self, handler_module, mock_ec2):
        """Verify error mentions 'not found' when AMI not found."""
        result = _deregister_nonexistent_ami(handler_module, mock_ec2)
        assert 'not found' in result['error'].lower()

    def test_deregisters_ami_returns_success(self, handler_module, mock_ec2):
        """Verify deregister_ami returns success=True."""
        _setup_ami_with_snapshots(mock_ec2)
        result = handler_module.deregister_ami('ami-test')
        assert result['success'] is True

    def test_deregisters_ami_returns_ami_id(self, handler_module, mock_ec2):
        """Verify deregister_ami returns the AMI ID."""
        _setup_ami_with_snapshots(mock_ec2)
        result = handler_module.deregister_ami('ami-test')
        assert result['ami_id'] == 'ami-test'

    def test_deregisters_ami_includes_first_snapshot(self, handler_module, mock_ec2):
        """Verify deleted_snapshots includes first snapshot."""
        _setup_ami_with_snapshots(mock_ec2)
        result = handler_module.deregister_ami('ami-test')
        assert 'snap-123' in result['deleted_snapshots']

    def test_deregisters_ami_includes_second_snapshot(self, handler_module, mock_ec2):
        """Verify deleted_snapshots includes second snapshot."""
        _setup_ami_with_snapshots(mock_ec2)
        result = handler_module.deregister_ami('ami-test')
        assert 'snap-456' in result['deleted_snapshots']

    def test_deregisters_ami_calls_deregister_image(self, handler_module, mock_ec2):
        """Verify deregister_image is called with correct AMI ID."""
        _setup_ami_with_snapshots(mock_ec2)
        handler_module.deregister_ami('ami-test')
        mock_ec2.deregister_image.assert_called_once_with(ImageId='ami-test')
        assert True  # Explicit pass

    def test_deregisters_ami_deletes_both_snapshots(self, handler_module, mock_ec2):
        """Verify both snapshots are deleted."""
        _setup_ami_with_snapshots(mock_ec2)
        handler_module.deregister_ami('ami-test')
        assert mock_ec2.delete_snapshot.call_count == 2

    def test_handles_snapshot_deletion_failure(self, handler_module, mock_ec2):
        """Verify handles snapshot deletion failure gracefully."""
        mock_ec2.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-test',
                'BlockDeviceMappings': [{'Ebs': {'SnapshotId': 'snap-123'}}]
            }]
        }
        mock_ec2.deregister_image.return_value = {}
        mock_ec2.delete_snapshot.side_effect = ClientError(
            {'Error': {'Code': 'InvalidSnapshot.NotFound', 'Message': 'Not found'}},
            'DeleteSnapshot'
        )
        result = handler_module.deregister_ami('ami-test')
        assert result['success'] is True

    def test_returns_error_on_deregister_failure(self, handler_module, mock_ec2):
        """Verify returns error when deregister fails."""
        mock_ec2.describe_images.return_value = {
            'Images': [{'ImageId': 'ami-test', 'BlockDeviceMappings': []}]
        }
        mock_ec2.deregister_image.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'DeregisterImage'
        )
        result = handler_module.deregister_ami('ami-test')
        assert result['success'] is False


class TestHandleEc2ImageDelete:
    """Tests for handle_ec2_image_delete function."""

    def test_returns_error_when_ami_id_missing(self, handler_module):
        """Verify returns 400 error when ami_id is missing."""
        event = {'pathParameters': {}}
        result = handler_module.handle_ec2_image_delete(event)
        assert result['statusCode'] == 400

    def test_returns_error_when_path_parameters_missing(self, handler_module):
        """Verify returns 400 error when pathParameters is missing."""
        event = {}
        result = handler_module.handle_ec2_image_delete(event)
        assert result['statusCode'] == 400


def _handle_options_request(handler_module):
    """Helper to handle an OPTIONS request."""
    event = {'httpMethod': 'OPTIONS', 'headers': {}}
    return handler_module.lambda_handler(event, None)


def _setup_delete_request(mock_ec2):
    """Setup mock EC2 for DELETE request."""
    mock_ec2.describe_images.return_value = {
        'Images': [{'ImageId': 'ami-123', 'BlockDeviceMappings': []}]
    }
    mock_ec2.deregister_image.return_value = {}


def _handle_delete_request(handler_module):
    """Helper to handle a DELETE request."""
    event = {
        'httpMethod': 'DELETE',
        'path': '/v1/runners/ec2/images/ami-123',
        'headers': {},
        'pathParameters': {'ami_id': 'ami-123'}
    }
    return handler_module.lambda_handler(event, None)


class TestLambdaHandler:
    """Tests for lambda_handler main entry point."""

    def test_options_returns_200(self, handler_module):
        """Verify OPTIONS request returns 200."""
        result = _handle_options_request(handler_module)
        assert result['statusCode'] == 200

    def test_options_has_allow_origin_header(self, handler_module):
        """Verify OPTIONS response has Access-Control-Allow-Origin header."""
        result = _handle_options_request(handler_module)
        assert 'Access-Control-Allow-Origin' in result['headers']

    def test_options_has_allow_methods_header(self, handler_module):
        """Verify OPTIONS response has Access-Control-Allow-Methods header."""
        result = _handle_options_request(handler_module)
        assert 'Access-Control-Allow-Methods' in result['headers']

    def test_enables_test_mode_from_header(self, handler_module):
        """Verify enables test mode from x-test-mode header."""
        event = {
            'httpMethod': 'GET',
            'path': '/v1/runners/ec2/images',
            'headers': {'x-test-mode': 'true'}
        }
        handler_module.set_client('ec2', MagicMock(
            describe_images=MagicMock(return_value={'Images': []})
        ))
        handler_module.lambda_handler(event, None)
        assert handler_module.is_test_mode() is True

    def test_routes_get_images_returns_200(self, handler_module, mock_ec2):
        """Verify GET /v1/runners/ec2/images returns 200."""
        mock_ec2.describe_images.return_value = {'Images': []}
        event = {
            'httpMethod': 'GET',
            'path': '/v1/runners/ec2/images',
            'headers': {}
        }
        result = handler_module.lambda_handler(event, None)
        assert result['statusCode'] == 200

    def test_routes_get_images_calls_describe_images(self, handler_module, mock_ec2):
        """Verify GET /v1/runners/ec2/images calls describe_images."""
        mock_ec2.describe_images.return_value = {'Images': []}
        event = {
            'httpMethod': 'GET',
            'path': '/v1/runners/ec2/images',
            'headers': {}
        }
        handler_module.lambda_handler(event, None)
        mock_ec2.describe_images.assert_called()
        assert True  # Explicit pass

    def test_routes_get_latest_to_get_latest_ami_details(
        self, handler_module, mock_ec2
    ):
        """Verify routes GET /v1/runners/ec2/images/latest returns 200."""
        mock_ec2.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-123',
                'Name': 'test',
                'State': 'available',
                'CreationDate': '2024-01-01T00:00:00Z',
                'Architecture': 'arm64',
                'Tags': []
            }]
        }
        event = {
            'httpMethod': 'GET',
            'path': '/v1/runners/ec2/images/latest',
            'headers': {}
        }
        result = handler_module.lambda_handler(event, None)
        assert result['statusCode'] == 200

    def test_delete_returns_200(self, handler_module, mock_ec2):
        """Verify DELETE request returns 200."""
        _setup_delete_request(mock_ec2)
        result = _handle_delete_request(handler_module)
        assert result['statusCode'] == 200

    def test_delete_returns_success_in_body(self, handler_module, mock_ec2):
        """Verify DELETE response body has success=True."""
        _setup_delete_request(mock_ec2)
        result = _handle_delete_request(handler_module)
        body = handler_module.json.loads(result['body'])
        assert body['success'] is True

    def test_delete_calls_deregister_image(self, handler_module, mock_ec2):
        """Verify DELETE calls deregister_image."""
        _setup_delete_request(mock_ec2)
        _handle_delete_request(handler_module)
        mock_ec2.deregister_image.assert_called_once_with(ImageId='ami-123')
        assert True  # Explicit pass

    def test_returns_404_for_unknown_route(self, handler_module):
        """Verify returns 404 for unknown routes."""
        event = {
            'httpMethod': 'GET',
            'path': '/v1/unknown/route',
            'headers': {}
        }
        result = handler_module.lambda_handler(event, None)
        assert result['statusCode'] == 404
