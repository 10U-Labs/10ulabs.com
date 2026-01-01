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


class TestGetGithubToken:
    """Tests for get_github_token function."""

    def test_returns_cached_token_if_available(self, handler_module):
        """Verify returns cached token without calling SSM."""
        handler_module._github_token_cache['value'] = 'cached-token'
        result = handler_module.get_github_token()
        assert result == 'cached-token'

    def test_fetches_token_from_ssm_when_not_cached(self, handler_module):
        """Verify fetches token from SSM when cache is empty."""
        handler_module._github_token_cache['value'] = ''
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {
            'Parameter': {'Value': 'ssm-token'}
        }
        with patch.object(handler_module.boto3, 'client', return_value=mock_ssm):
            result = handler_module.get_github_token()
        assert result == 'ssm-token'
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


class TestTriggerGithubWorkflow:
    """Tests for trigger_github_workflow function."""

    def test_returns_error_when_no_token(self, handler_module):
        """Verify returns error when GitHub token is not available."""
        handler_module._github_token_cache['value'] = ''
        with patch.object(handler_module.boto3, 'client') as mock_client:
            mock_ssm = MagicMock()
            mock_ssm.get_parameter.side_effect = ClientError(
                {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
                'GetParameter'
            )
            mock_client.return_value = mock_ssm
            result = handler_module.trigger_github_workflow('test.yml', {'ref': 'main'})
        assert result['success'] is False
        assert 'GITHUB_TOKEN' in result['error']

    def test_returns_success_on_204_response(self, handler_module):
        """Verify returns success when GitHub API returns 204."""
        handler_module._github_token_cache['value'] = 'test-token'
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch.object(handler_module.urllib.request, 'urlopen', return_value=mock_response):
            result = handler_module.trigger_github_workflow('test.yml', {'ref': 'main'})
        assert result['success'] is True

    def test_returns_error_on_non_204_response(self, handler_module):
        """Verify returns error when GitHub API returns non-204."""
        handler_module._github_token_cache['value'] = 'test-token'
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch.object(handler_module.urllib.request, 'urlopen', return_value=mock_response):
            result = handler_module.trigger_github_workflow('test.yml', {'ref': 'main'})
        assert result['success'] is False
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


class TestHandlePostRequest:
    """Tests for handle_post_request function."""

    def test_returns_mock_response_in_test_mode(self, handler_module):
        """Verify returns mock response when test mode is enabled."""
        handler_module.set_test_mode(True)
        event = {'path': '/v1/runners/ec2/images'}
        result = handler_module.handle_post_request(event, lambda x: x)
        assert result['statusCode'] == 200
        body = handler_module.json.loads(result['body'])
        assert body['test_mode'] is True

    def test_calls_handler_func_when_not_test_mode(self, handler_module):
        """Verify calls handler function when not in test mode."""
        handler_module.set_test_mode(False)
        event = {'path': '/v1/runners/ec2/images', 'body': '{}'}
        mock_handler = MagicMock(return_value={'result': 'success'})
        result = handler_module.handle_post_request(event, mock_handler)
        mock_handler.assert_called_once()
        assert result['statusCode'] == 200

    def test_returns_500_on_exception(self, handler_module):
        """Verify returns 500 error on exception."""
        handler_module.set_test_mode(False)
        event = {'path': '/v1/runners/ec2/images', 'body': '{}'}
        mock_handler = MagicMock(side_effect=ValueError('Test error'))
        result = handler_module.handle_post_request(event, mock_handler)
        assert result['statusCode'] == 500


class TestListAmisErrorHandling:
    """Tests for list_amis error handling."""

    def test_returns_error_on_client_error(self, handler_module, mock_ec2):
        """Verify returns error response on EC2 client error."""
        mock_ec2.describe_images.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'DescribeImages'
        )
        result = handler_module.list_amis()
        assert result['success'] is False
        assert 'error' in result


class TestGetLatestAmiDetailsErrorHandling:
    """Tests for get_latest_ami_details error handling."""

    def test_returns_error_on_client_error(self, handler_module, mock_ec2):
        """Verify returns error response on EC2 client error."""
        mock_ec2.describe_images.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'DescribeImages'
        )
        result = handler_module.get_latest_ami_details()
        assert result['success'] is False
        assert 'error' in result


class TestDeregisterAmi:
    """Tests for deregister_ami function."""

    def test_returns_error_when_ami_not_found(self, handler_module, mock_ec2):
        """Verify returns error when AMI not found."""
        mock_ec2.describe_images.return_value = {'Images': []}
        result = handler_module.deregister_ami('ami-nonexistent')
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_deregisters_ami_and_deletes_snapshots(self, handler_module, mock_ec2):
        """Verify deregisters AMI and deletes associated snapshots."""
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

        result = handler_module.deregister_ami('ami-test')

        assert result['success'] is True
        assert result['ami_id'] == 'ami-test'
        assert 'snap-123' in result['deleted_snapshots']
        assert 'snap-456' in result['deleted_snapshots']
        mock_ec2.deregister_image.assert_called_once_with(ImageId='ami-test')
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

        # Should not raise, just log warning
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


class TestLambdaHandler:
    """Tests for lambda_handler main entry point."""

    def test_handles_options_request(self, handler_module):
        """Verify handles OPTIONS request for CORS preflight."""
        event = {'httpMethod': 'OPTIONS', 'headers': {}}
        result = handler_module.lambda_handler(event, None)
        assert result['statusCode'] == 200
        assert 'Access-Control-Allow-Origin' in result['headers']
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

    def test_routes_get_images_to_list_amis(self, handler_module, mock_ec2):
        """Verify routes GET /v1/runners/ec2/images to list_amis."""
        mock_ec2.describe_images.return_value = {'Images': []}
        event = {
            'httpMethod': 'GET',
            'path': '/v1/runners/ec2/images',
            'headers': {}
        }
        result = handler_module.lambda_handler(event, None)
        assert result['statusCode'] == 200
        mock_ec2.describe_images.assert_called()

    def test_routes_get_latest_to_get_latest_ami_details(
        self, handler_module, mock_ec2
    ):
        """Verify routes GET /v1/runners/ec2/images/latest to get_latest_ami_details."""
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

    def test_routes_delete_to_handle_ec2_image_delete(
        self, handler_module, mock_ec2
    ):
        """Verify routes DELETE to handle_ec2_image_delete."""
        # Set up mock to return an AMI that can be deleted
        mock_ec2.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-123',
                'BlockDeviceMappings': []
            }]
        }
        mock_ec2.deregister_image.return_value = {}
        event = {
            'httpMethod': 'DELETE',
            'path': '/v1/runners/ec2/images/ami-123',
            'headers': {},
            'pathParameters': {'ami_id': 'ami-123'}
        }
        result = handler_module.lambda_handler(event, None)
        # Verify routing worked - should get 200 with success response
        assert result['statusCode'] == 200
        body = handler_module.json.loads(result['body'])
        assert body['success'] is True
        mock_ec2.deregister_image.assert_called_once_with(ImageId='ami-123')

    def test_returns_404_for_unknown_route(self, handler_module):
        """Verify returns 404 for unknown routes."""
        event = {
            'httpMethod': 'GET',
            'path': '/v1/unknown/route',
            'headers': {}
        }
        result = handler_module.lambda_handler(event, None)
        assert result['statusCode'] == 404
