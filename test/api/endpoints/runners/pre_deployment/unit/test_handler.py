"""Unit tests for /v1/runners Lambda handler."""
import json
import sys
import urllib.error
from unittest.mock import MagicMock, patch, Mock

import pytest

from repo_utils import REPO_ROOT

# Add the lambda directory to the path for imports
LAMBDA_DIR = REPO_ROOT / 'src' / 'api' / 'endpoints' / 'runners' / 'lambda'
sys.path.insert(0, str(LAMBDA_DIR))

# Add lib/python for runner_labels
LIB_PYTHON = REPO_ROOT / 'lib' / 'python'
sys.path.insert(0, str(LIB_PYTHON))


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set required environment variables."""
    monkeypatch.setenv('API_BASE_URL', 'https://api.example.com')
    monkeypatch.setenv('API_KEY_PARAMETER_NAME', '/test/api-key')


@pytest.fixture
def mock_ssm_client():
    """Mock SSM client for API key retrieval."""
    with patch('boto3.client') as mock_client:
        ssm_mock = MagicMock()
        ssm_mock.get_parameter.return_value = {
            'Parameter': {'Value': 'test-api-key'}
        }
        mock_client.return_value = ssm_mock
        yield ssm_mock


@pytest.fixture
def sqs_event():
    """Create a sample SQS event."""
    return {
        'Records': [{
            'eventSource': 'aws:sqs',
            'messageId': 'test-123',
            'body': json.dumps({
                'job_id': 12345,
                'job_labels': ['self-hosted', 'linux', 'ec2'],
                'github_repo': 'org/repo',
                'run_id': 999
            })
        }]
    }


@pytest.fixture
def sqs_event_ecs():
    """Create a sample SQS event with ECS labels."""
    return {
        'Records': [{
            'eventSource': 'aws:sqs',
            'messageId': 'test-456',
            'body': json.dumps({
                'job_id': 67890,
                'job_labels': ['ecs', 'fargate', 'arm', 'spot', 'runner-123'],
                'github_repo': 'org/repo',
                'run_id': 1000
            })
        }]
    }


@pytest.fixture
def handler_module(mock_env_vars):
    """Import handler module with mocked environment."""
    # Clear any cached import
    if 'handler' in sys.modules:
        del sys.modules['handler']
    import handler
    # Reset the API key cache
    handler._api_key_cache.clear()
    return handler


class TestSqsEventHandling:
    """Tests for SQS event handling."""

    def test_sqs_event_has_records(self, mock_env_vars, mock_ssm_client, sqs_event):
        """Test that SQS events have records."""
        records = sqs_event.get('Records', [])
        assert len(records) > 0

    def test_sqs_event_has_correct_source(self, mock_env_vars, mock_ssm_client, sqs_event):
        """Test that SQS events have correct eventSource."""
        records = sqs_event.get('Records', [])
        assert records[0].get('eventSource') == 'aws:sqs'


class TestRunnerLabels:
    """Tests for runner label parsing integration."""

    def test_runner_labels_import(self):
        """Test that runner_labels module can be imported."""
        import runner_labels
        assert hasattr(runner_labels, 'get_runner_type_from_labels')

    def test_ec2_label_returns_ec2_runner_type(self):
        """Test EC2 labels return ec2 runner type."""
        import runner_labels
        job_labels = ['ec2', 'general-purpose', 'arm', 'spot', 'runner-12345']
        runner_type, _ = runner_labels.get_runner_type_from_labels(job_labels)
        assert runner_type == 'ec2'

    def test_ec2_label_returns_ec2_endpoint(self):
        """Test EC2 labels return ec2 endpoint."""
        import runner_labels
        job_labels = ['ec2', 'general-purpose', 'arm', 'spot', 'runner-12345']
        _, endpoint = runner_labels.get_runner_type_from_labels(job_labels)
        assert endpoint == 'ec2'

    def test_fargate_label_returns_fargate_runner_type(self):
        """Test Fargate labels return fargate runner type."""
        import runner_labels
        job_labels = ['ecs', 'fargate', 'arm', 'spot', 'runner-12345']
        runner_type, _ = runner_labels.get_runner_type_from_labels(job_labels)
        assert runner_type == 'fargate'

    def test_fargate_label_returns_ecs_endpoint(self):
        """Test Fargate labels return ecs endpoint."""
        import runner_labels
        job_labels = ['ecs', 'fargate', 'arm', 'spot', 'runner-12345']
        _, endpoint = runner_labels.get_runner_type_from_labels(job_labels)
        assert endpoint == 'ecs'

    def test_no_matching_labels_returns_none_runner_type(self):
        """Test unmatched labels return None runner type."""
        import runner_labels
        job_labels = ['self-hosted', 'windows']
        runner_type, _ = runner_labels.get_runner_type_from_labels(job_labels)
        assert runner_type is None

    def test_no_matching_labels_returns_none_endpoint(self):
        """Test unmatched labels return None endpoint."""
        import runner_labels
        job_labels = ['self-hosted', 'windows']
        _, endpoint = runner_labels.get_runner_type_from_labels(job_labels)
        assert endpoint is None


class TestGetApiKey:
    """Tests for _get_api_key function."""

    def test_get_api_key_fetches_from_ssm(self, handler_module, mock_ssm_client):
        """Test _get_api_key fetches from SSM Parameter Store."""
        api_key = handler_module._get_api_key()
        assert api_key == 'test-api-key'

    def test_get_api_key_returns_cached_value(self, handler_module, mock_ssm_client):
        """Test _get_api_key returns cached value on second call."""
        handler_module._get_api_key()
        api_key = handler_module._get_api_key()
        assert api_key == 'test-api-key'

    def test_get_api_key_only_calls_ssm_once(self, handler_module, mock_ssm_client):
        """Test _get_api_key only calls SSM once when called multiple times."""
        handler_module._get_api_key()
        handler_module._get_api_key()
        assert mock_ssm_client.get_parameter.call_count == 1

    def test_get_api_key_stores_in_cache(self, handler_module, mock_ssm_client):
        """Test _get_api_key stores result in cache."""
        handler_module._get_api_key()
        assert 'api_key' in handler_module._api_key_cache

    def test_get_api_key_cached_value_correct(self, handler_module, mock_ssm_client):
        """Test _get_api_key caches correct value."""
        handler_module._get_api_key()
        assert handler_module._api_key_cache['api_key'] == 'test-api-key'


class TestRouteToRunner:
    """Tests for _route_to_runner function."""

    def test_route_to_runner_returns_200_status_code(self, handler_module, mock_ssm_client):
        """Test _route_to_runner returns 200 status code on success."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch('urllib.request.urlopen', return_value=mock_response):
            result = handler_module._route_to_runner('ec2', {'job_id': 123})

        assert result['statusCode'] == 200

    def test_route_to_runner_returns_response_body(self, handler_module, mock_ssm_client):
        """Test _route_to_runner returns success in response body."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch('urllib.request.urlopen', return_value=mock_response):
            result = handler_module._route_to_runner('ec2', {'job_id': 123})

        assert 'success' in result['body']

    def test_route_to_runner_http_error(self, handler_module, mock_ssm_client):
        """Test _route_to_runner handles HTTP errors."""
        mock_error = urllib.error.HTTPError(
            url='https://api.example.com/v1/runners/ec2',
            code=500,
            msg='Internal Server Error',
            hdrs={},
            fp=None
        )

        with patch('urllib.request.urlopen', side_effect=mock_error):
            result = handler_module._route_to_runner('ec2', {'job_id': 123})

        assert result['statusCode'] == 500

    def test_route_to_runner_url_error(self, handler_module, mock_ssm_client):
        """Test _route_to_runner raises on URL errors."""
        mock_error = urllib.error.URLError('Connection refused')

        with patch('urllib.request.urlopen', side_effect=mock_error):
            with pytest.raises(urllib.error.URLError):
                handler_module._route_to_runner('ec2', {'job_id': 123})

    def test_route_to_runner_includes_api_key_header(self, handler_module, mock_ssm_client):
        """Test _route_to_runner includes x-api-key header."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
            handler_module._route_to_runner('ec2', {'job_id': 123})
            request = mock_urlopen.call_args[0][0]
            assert request.get_header('X-api-key') == 'test-api-key'


class TestProcessRunnerRequest:
    """Tests for _process_runner_request function."""

    def test_process_runner_request_ec2_labels(self, handler_module, mock_ssm_client):
        """Test _process_runner_request routes EC2 labels correctly."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"runner_type": "ec2"}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        message = {
            'job_id': 123,
            'job_labels': ['ec2', 'general-purpose', 'arm', 'spot', 'runner-1'],
            'github_repo': 'org/repo',
            'run_id': 456
        }

        with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
            handler_module._process_runner_request(message)
            request = mock_urlopen.call_args[0][0]
            assert '/v1/runners/ec2' in request.full_url

    def test_process_runner_request_ecs_labels(self, handler_module, mock_ssm_client):
        """Test _process_runner_request routes ECS labels correctly."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"runner_type": "fargate"}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        message = {
            'job_id': 123,
            'job_labels': ['ecs', 'fargate', 'arm', 'spot', 'runner-1'],
            'github_repo': 'org/repo',
            'run_id': 456
        }

        with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
            handler_module._process_runner_request(message)
            request = mock_urlopen.call_args[0][0]
            assert '/v1/runners/ecs' in request.full_url

    def test_process_runner_request_no_matching_labels_returns_200(
            self, handler_module, mock_ssm_client):
        """Test _process_runner_request returns 200 for unmatched labels."""
        message = {
            'job_id': 123,
            'job_labels': ['self-hosted', 'windows'],
            'github_repo': 'org/repo',
            'run_id': 456
        }

        result = handler_module._process_runner_request(message)
        assert result['statusCode'] == 200

    def test_process_runner_request_no_matching_labels_message(
            self, handler_module, mock_ssm_client):
        """Test _process_runner_request returns correct message for unmatched labels."""
        message = {
            'job_id': 123,
            'job_labels': ['self-hosted', 'windows'],
            'github_repo': 'org/repo',
            'run_id': 456
        }

        result = handler_module._process_runner_request(message)
        body = json.loads(result['body'])
        assert body['message'] == 'No matching runner type'

    def test_process_runner_request_payload_includes_job_id(
            self, handler_module, mock_ssm_client):
        """Test _process_runner_request includes job_id in payload."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        message = {
            'job_id': 123,
            'job_labels': ['ec2', 'general-purpose', 'arm', 'spot', 'runner-1'],
            'github_repo': 'org/repo',
            'run_id': 456
        }

        with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
            handler_module._process_runner_request(message)
            request = mock_urlopen.call_args[0][0]
            payload = json.loads(request.data.decode('utf-8'))
            assert payload['job_id'] == 123

    def test_process_runner_request_payload_includes_github_repo(
            self, handler_module, mock_ssm_client):
        """Test _process_runner_request includes github_repo in payload."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        message = {
            'job_id': 123,
            'job_labels': ['ec2', 'general-purpose', 'arm', 'spot', 'runner-1'],
            'github_repo': 'org/repo',
            'run_id': 456
        }

        with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
            handler_module._process_runner_request(message)
            request = mock_urlopen.call_args[0][0]
            payload = json.loads(request.data.decode('utf-8'))
            assert payload['github_repo'] == 'org/repo'

    def test_process_runner_request_payload_includes_run_id(
            self, handler_module, mock_ssm_client):
        """Test _process_runner_request includes run_id in payload."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        message = {
            'job_id': 123,
            'job_labels': ['ec2', 'general-purpose', 'arm', 'spot', 'runner-1'],
            'github_repo': 'org/repo',
            'run_id': 456
        }

        with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
            handler_module._process_runner_request(message)
            request = mock_urlopen.call_args[0][0]
            payload = json.loads(request.data.decode('utf-8'))
            assert payload['run_id'] == 456

    def test_process_runner_request_payload_includes_runner_type(
            self, handler_module, mock_ssm_client):
        """Test _process_runner_request includes runner_type in payload."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        message = {
            'job_id': 123,
            'job_labels': ['ec2', 'general-purpose', 'arm', 'spot', 'runner-1'],
            'github_repo': 'org/repo',
            'run_id': 456
        }

        with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
            handler_module._process_runner_request(message)
            request = mock_urlopen.call_args[0][0]
            payload = json.loads(request.data.decode('utf-8'))
            assert payload['runner_type'] == 'ec2'


class TestHandleSqsEvent:
    """Tests for _handle_sqs_event function."""

    def test_handle_sqs_event_processes_all_records(self, handler_module, mock_ssm_client):
        """Test _handle_sqs_event processes all SQS records."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'job_id': 1,
                        'job_labels': ['ec2', 'general-purpose', 'arm', 'spot', 'runner-1'],
                        'github_repo': 'org/repo',
                        'run_id': 100
                    })
                },
                {
                    'messageId': 'msg-2',
                    'body': json.dumps({
                        'job_id': 2,
                        'job_labels': ['ecs', 'fargate', 'arm', 'spot', 'runner-2'],
                        'github_repo': 'org/repo',
                        'run_id': 101
                    })
                }
            ]
        }

        with patch('urllib.request.urlopen', return_value=mock_response):
            result = handler_module._handle_sqs_event(event)

        body = json.loads(result['body'])
        assert len(body['results']) == 2

    def test_handle_sqs_event_handles_json_decode_error(self, handler_module, mock_ssm_client):
        """Test _handle_sqs_event handles invalid JSON in record body."""
        event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': 'invalid json'
                }
            ]
        }

        result = handler_module._handle_sqs_event(event)

        body = json.loads(result['body'])
        assert 'error' in body['results'][0]

    def test_handle_sqs_event_returns_message_id(self, handler_module, mock_ssm_client):
        """Test _handle_sqs_event returns messageId for each record."""
        event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'job_id': 1,
                        'job_labels': ['self-hosted', 'windows'],
                        'github_repo': 'org/repo',
                        'run_id': 100
                    })
                }
            ]
        }

        result = handler_module._handle_sqs_event(event)

        body = json.loads(result['body'])
        assert body['results'][0]['messageId'] == 'msg-1'

    def test_handle_sqs_event_returns_result_for_record(self, handler_module, mock_ssm_client):
        """Test _handle_sqs_event returns result for each record."""
        event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'job_id': 1,
                        'job_labels': ['self-hosted', 'windows'],
                        'github_repo': 'org/repo',
                        'run_id': 100
                    })
                }
            ]
        }

        result = handler_module._handle_sqs_event(event)

        body = json.loads(result['body'])
        assert 'result' in body['results'][0]


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    def test_lambda_handler_sqs_event_returns_200(
            self, handler_module, mock_ssm_client, sqs_event):
        """Test lambda_handler returns 200 for SQS events."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch('urllib.request.urlopen', return_value=mock_response):
            result = handler_module.lambda_handler(sqs_event, None)

        assert result['statusCode'] == 200

    def test_lambda_handler_sqs_event_returns_results(
            self, handler_module, mock_ssm_client, sqs_event):
        """Test lambda_handler returns results in body for SQS events."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch('urllib.request.urlopen', return_value=mock_response):
            result = handler_module.lambda_handler(sqs_event, None)

        body = json.loads(result['body'])
        assert 'results' in body

    def test_lambda_handler_non_sqs_event_returns_400(self, handler_module, mock_ssm_client):
        """Test lambda_handler returns 400 for non-SQS events."""
        event = {'some': 'data'}
        result = handler_module.lambda_handler(event, None)
        assert result['statusCode'] == 400

    def test_lambda_handler_non_sqs_event_returns_error(self, handler_module, mock_ssm_client):
        """Test lambda_handler returns error message for non-SQS events."""
        event = {'some': 'data'}
        result = handler_module.lambda_handler(event, None)
        body = json.loads(result['body'])
        assert body['error'] == 'Expected SQS event'

    def test_lambda_handler_empty_records_returns_400(self, handler_module, mock_ssm_client):
        """Test lambda_handler returns 400 for empty Records."""
        event = {'Records': []}
        result = handler_module.lambda_handler(event, None)
        assert result['statusCode'] == 400
