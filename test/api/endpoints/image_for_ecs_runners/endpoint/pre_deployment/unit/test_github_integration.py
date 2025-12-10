"""Tests for GitHub integration functions."""
import sys
import urllib.error
from unittest.mock import MagicMock, patch

handler = sys.modules['handler']


class TestGetGithubToken:
    """Tests for get_github_token function."""

    def test_fetches_token_from_ssm(self, mock_ssm_client):
        """Test that token is fetched from SSM."""
        mock_ssm_client.get_parameter.return_value = {
            'Parameter': {'Value': 'ssm-token'}
        }

        with patch('handler.boto3') as mock_boto3:
            mock_boto3.client.return_value = mock_ssm_client
            with patch.dict('os.environ', {'GITHUB_TOKEN_SECRET_NAME': '/github/token'}):
                result = handler.get_github_token()

        assert result == 'ssm-token'

    def test_returns_token_value(self, mock_ssm_client):
        """Test that token value from SSM is returned."""
        mock_ssm_client.get_parameter.return_value = {
            'Parameter': {'Value': 'my-secret-token'}
        }

        with patch('handler.boto3') as mock_boto3:
            mock_boto3.client.return_value = mock_ssm_client
            with patch.dict('os.environ', {'GITHUB_TOKEN_SECRET_NAME': '/github/token'}):
                result = handler.get_github_token()

        assert 'token' in result.lower() or result == 'my-secret-token'


class TestTriggerGithubWorkflow:
    """Tests for trigger_github_workflow function."""

    def test_returns_error_when_no_token(self):
        """Test that error is returned when no token available."""
        with patch('handler.get_github_token', return_value=''):
            with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                result = handler.trigger_github_workflow('workflow.yml', {'ref': 'main'})

        assert result['success'] is False
        assert 'not configured' in result['error'].lower()

    def test_triggers_workflow_successfully(self):
        """Test that workflow is triggered successfully."""
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch('handler.get_github_token', return_value='valid-token'):
            with patch('urllib.request.urlopen', return_value=mock_response):
                with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                    result = handler.trigger_github_workflow('workflow.yml', {'ref': 'main'})

        assert result['success'] is True
        assert 'triggered' in result['message'].lower()

    def test_constructs_correct_url(self):
        """Test that correct URL is constructed."""
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch('handler.get_github_token', return_value='valid-token'):
            with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
                with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                    handler.trigger_github_workflow('test.yml', {'ref': 'main'})

        request = mock_urlopen.call_args[0][0]
        expected_url = (
            'https://api.github.com/repos/org/repo/actions/workflows/test.yml/dispatches'
        )
        assert request.full_url == expected_url

    def test_includes_authorization_header(self):
        """Test that authorization header is included."""
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch('handler.get_github_token', return_value='valid-token'):
            with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
                with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                    handler.trigger_github_workflow('test.yml', {'ref': 'main'})

        request = mock_urlopen.call_args[0][0]
        assert request.get_header('Authorization') == 'Bearer valid-token'

    def test_returns_error_on_non_204_status(self):
        """Test that error is returned for non-204 status."""
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch('handler.get_github_token', return_value='valid-token'):
            with patch('urllib.request.urlopen', return_value=mock_response):
                with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                    result = handler.trigger_github_workflow('test.yml', {'ref': 'main'})

        assert result['success'] is False
        assert 'unexpected' in result['error'].lower()

    def test_handles_url_error(self):
        """Test that URLError is handled."""
        with patch('handler.get_github_token', return_value='valid-token'):
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_urlopen.side_effect = urllib.error.URLError('Connection failed')
                with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                    result = handler.trigger_github_workflow('test.yml', {'ref': 'main'})

        assert result['success'] is False
        assert 'error' in result

    def test_handles_http_error(self):
        """Test that HTTPError is handled."""
        with patch('handler.get_github_token', return_value='valid-token'):
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_urlopen.side_effect = urllib.error.HTTPError(
                    'url', 401, 'Unauthorized', {}, None
                )
                with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                    result = handler.trigger_github_workflow('test.yml', {'ref': 'main'})

        assert result['success'] is False

    def test_uses_post_method(self):
        """Test that POST method is used."""
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch('handler.get_github_token', return_value='valid-token'):
            with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
                with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                    handler.trigger_github_workflow('test.yml', {'ref': 'main'})

        request = mock_urlopen.call_args[0][0]
        assert request.method == 'POST'


class TestTriggerEcsImageBuild:
    """Tests for trigger_ecs_image_build function."""

    def test_triggers_correct_workflow(self):
        """Test that correct workflow is triggered."""
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch('handler.get_github_token', return_value='valid-token'):
            with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
                with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                    handler.trigger_ecs_image_build({})

        request = mock_urlopen.call_args[0][0]
        assert 'endpoint_v1_image_for_ecs_runners_post.yml' in request.full_url

    def test_uses_main_branch(self):
        """Test that main branch is used."""
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch('handler.get_github_token', return_value='valid-token'):
            with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
                with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                    handler.trigger_ecs_image_build({})

        request = mock_urlopen.call_args[0][0]
        assert b'"ref": "main"' in request.data
