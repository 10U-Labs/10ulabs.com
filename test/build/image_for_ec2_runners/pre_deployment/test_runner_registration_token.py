from unittest.mock import Mock, patch
import urllib.error
import json


class TestGetRunnerRegistrationToken:

    def test_successful_token_retrieval(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = json.dumps({'token': 'test-registration-token'}).encode()
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            token = v1_handler.get_runner_registration_token('ghp_test', 'owner/repo')

            assert token == 'test-registration-token'

    def test_http_error_401(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError('url', 401, 'Unauthorized', {}, None)

            token = v1_handler.get_runner_registration_token('ghp_test', 'owner/repo')

            assert token == ''

    def test_http_error_403(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError('url', 403, 'Forbidden', {}, None)

            token = v1_handler.get_runner_registration_token('ghp_test', 'owner/repo')

            assert token == ''

    def test_url_error_timeout(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('timeout')

            token = v1_handler.get_runner_registration_token('ghp_test', 'owner/repo')

            assert token == ''

    def test_malformed_json_response(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = b'not-json'
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            token = v1_handler.get_runner_registration_token('ghp_test', 'owner/repo')

            assert token == ''

    def test_missing_token_in_response(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = json.dumps({'expires_at': '2024-01-01'}).encode()
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            token = v1_handler.get_runner_registration_token('ghp_test', 'owner/repo')

            assert token == ''
