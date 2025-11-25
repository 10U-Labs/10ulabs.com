from unittest.mock import Mock, patch
import urllib.error
import json


class TestTriggerAmiCreation:

    def test_successful_api_call(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen, \
             patch.dict('os.environ', {'API_DOMAIN': 'api.test.com'}), \
             patch.object(v1_handler, 'get_api_key', return_value='test-api-key'):

            mock_response = Mock()
            mock_response.read.return_value = json.dumps({'success': True}).encode()
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = v1_handler.trigger_ami_creation()

            assert result['success'] is True

    def test_uses_correct_api_domain(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen, \
             patch.dict('os.environ', {'API_DOMAIN': 'api.custom.com'}), \
             patch.object(v1_handler, 'get_api_key', return_value='test-api-key'):

            mock_response = Mock()
            mock_response.read.return_value = json.dumps({}).encode()
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            v1_handler.trigger_ami_creation()

            call_args = mock_urlopen.call_args[0][0]
            assert 'api.custom.com' in call_args.full_url

    def test_timeout_handling(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen, \
             patch.dict('os.environ', {'API_DOMAIN': 'api.test.com'}), \
             patch.object(v1_handler, 'get_api_key', return_value='test-api-key'):
            mock_urlopen.side_effect = urllib.error.URLError('timeout')

            result = v1_handler.trigger_ami_creation()

            assert result['success'] is False

    def test_http_error_handling(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen, \
             patch.dict('os.environ', {'API_DOMAIN': 'api.test.com'}), \
             patch.object(v1_handler, 'get_api_key', return_value='test-api-key'):
            mock_urlopen.side_effect = urllib.error.HTTPError('url', 500, 'Internal Error', {}, None)

            result = v1_handler.trigger_ami_creation()

            assert result['success'] is False
