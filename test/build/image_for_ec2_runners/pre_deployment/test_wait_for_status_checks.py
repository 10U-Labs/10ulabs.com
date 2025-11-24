from unittest.mock import Mock, patch
import urllib.error
import pytest


class TestGetImdsToken:

    def test_success(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = b'test-token-123'
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            token = wait_for_status_checks.get_imds_token()

            assert token == 'test-token-123'

    def test_calls_urlopen(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = b'test-token-123'
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            wait_for_status_checks.get_imds_token()

            mock_urlopen.assert_called_once()

    def test_timeout(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('timeout')

            with pytest.raises(urllib.error.URLError):
                wait_for_status_checks.get_imds_token()

    def test_http_error(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError('url', 403, 'Forbidden', {}, None)

            with pytest.raises(urllib.error.HTTPError):
                wait_for_status_checks.get_imds_token()


class TestGetMetadata:

    def test_success(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = b'i-1234567890'
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = wait_for_status_checks.get_metadata('test-token', 'instance-id')

            assert result == 'i-1234567890'

    def test_different_paths(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = b'us-east-1a'
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = wait_for_status_checks.get_metadata('test-token', 'placement/region')

            assert result == 'us-east-1a'

    def test_timeout(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('timeout')

            with pytest.raises(urllib.error.URLError):
                wait_for_status_checks.get_metadata('test-token', 'instance-id')


class TestMain:

    def test_successful_completion(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen, \
             patch('subprocess.run') as mock_run:

            mock_token_response = Mock()
            mock_token_response.read.return_value = b'test-token'
            mock_token_response.__enter__ = Mock(return_value=mock_token_response)
            mock_token_response.__exit__ = Mock(return_value=False)

            mock_instance_response = Mock()
            mock_instance_response.read.return_value = b'i-123456'
            mock_instance_response.__enter__ = Mock(return_value=mock_instance_response)
            mock_instance_response.__exit__ = Mock(return_value=False)

            mock_region_response = Mock()
            mock_region_response.read.return_value = b'us-east-1'
            mock_region_response.__enter__ = Mock(return_value=mock_region_response)
            mock_region_response.__exit__ = Mock(return_value=False)

            mock_urlopen.side_effect = [mock_token_response, mock_instance_response, mock_region_response]

            mock_run_result = Mock()
            mock_run_result.returncode = 0
            mock_run_result.stdout = 'ok\tok'
            mock_run.return_value = mock_run_result

            result = wait_for_status_checks.main()

            assert result == 0

    def test_imds_token_failure(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('Connection failed')

            with pytest.raises(SystemExit) as exc_info:
                wait_for_status_checks.main()

            assert exc_info.value.code == 1

    def test_max_attempts_reached(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen, \
             patch('subprocess.run') as mock_run, \
             patch('time.sleep'):

            mock_token_response = Mock()
            mock_token_response.read.return_value = b'test-token'
            mock_token_response.__enter__ = Mock(return_value=mock_token_response)
            mock_token_response.__exit__ = Mock(return_value=False)

            mock_instance_response = Mock()
            mock_instance_response.read.return_value = b'i-123456'
            mock_instance_response.__enter__ = Mock(return_value=mock_instance_response)
            mock_instance_response.__exit__ = Mock(return_value=False)

            mock_region_response = Mock()
            mock_region_response.read.return_value = b'us-east-1'
            mock_region_response.__enter__ = Mock(return_value=mock_region_response)
            mock_region_response.__exit__ = Mock(return_value=False)

            mock_urlopen.side_effect = [mock_token_response, mock_instance_response, mock_region_response]

            mock_run_result = Mock()
            mock_run_result.returncode = 0
            mock_run_result.stdout = 'initializing\tinitializing'
            mock_run.return_value = mock_run_result

            with pytest.raises(SystemExit) as exc_info:
                wait_for_status_checks.main()

            assert exc_info.value.code == 1
