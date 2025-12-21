"""Tests for GitHub integration functions."""
import sys
import urllib.error
from unittest.mock import patch

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

    def test_returns_error_when_no_token_success_false(self):
        """Test that success is False when no token available."""
        with patch('handler.get_github_token', return_value=''):
            with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                result = handler.trigger_github_workflow('workflow.yml', {'ref': 'main'})

        assert result['success'] is False

    def test_returns_error_when_no_token_error_message(self):
        """Test that error message mentions not configured."""
        with patch('handler.get_github_token', return_value=''):
            with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                result = handler.trigger_github_workflow('workflow.yml', {'ref': 'main'})

        assert 'not configured' in result['error'].lower()

    def test_triggers_workflow_successfully_returns_success(self, mock_http_response_204):
        """Test that workflow trigger returns success True."""
        with patch('handler.get_github_token', return_value='valid-token'):
            with patch('urllib.request.urlopen', return_value=mock_http_response_204):
                with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                    result = handler.trigger_github_workflow('workflow.yml', {'ref': 'main'})

        assert result['success'] is True

    def test_triggers_workflow_successfully_message(self, mock_http_response_204):
        """Test that workflow trigger returns triggered message."""
        with patch('handler.get_github_token', return_value='valid-token'):
            with patch('urllib.request.urlopen', return_value=mock_http_response_204):
                with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                    result = handler.trigger_github_workflow('workflow.yml', {'ref': 'main'})

        assert 'triggered' in result['message'].lower()

    def test_constructs_correct_url(self, github_workflow_trigger_context):
        """Test that correct URL is constructed."""
        def trigger():
            handler.trigger_github_workflow('test.yml', {'ref': 'main'})

        with github_workflow_trigger_context(trigger) as request:
            expected_url = (
                'https://api.github.com/repos/org/repo/actions/workflows/test.yml/dispatches'
            )
            assert request.full_url == expected_url

    def test_includes_authorization_header(self, github_workflow_trigger_context):
        """Test that authorization header is included."""
        def trigger():
            handler.trigger_github_workflow('test.yml', {'ref': 'main'})

        with github_workflow_trigger_context(trigger) as request:
            assert request.get_header('Authorization') == 'Bearer valid-token'

    def test_returns_error_on_non_204_status_success_false(
        self, trigger_workflow_with_response
    ):
        """Test that non-204 status returns success False."""
        result = trigger_workflow_with_response(500)

        assert result['success'] is False

    def test_returns_error_on_non_204_status_error_message(
        self, trigger_workflow_with_response
    ):
        """Test that non-204 status returns unexpected error."""
        result = trigger_workflow_with_response(500)

        assert 'unexpected' in result['error'].lower()

    def test_handles_url_error_success_false(self, url_error_workflow_result):
        """Test that URLError returns success False."""
        assert url_error_workflow_result['success'] is False

    def test_handles_url_error_has_error_key(self, url_error_workflow_result):
        """Test that URLError result has error key."""
        assert 'error' in url_error_workflow_result

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

    def test_uses_post_method(self, github_workflow_trigger_context):
        """Test that POST method is used."""
        def trigger():
            handler.trigger_github_workflow('test.yml', {'ref': 'main'})

        with github_workflow_trigger_context(trigger) as request:
            assert request.method == 'POST'


class TestTriggerEcsImageBuild:
    """Tests for trigger_ecs_image_build function."""

    def test_triggers_correct_workflow(self, github_workflow_trigger_context):
        """Test that correct workflow is triggered."""
        def trigger():
            handler.trigger_ecs_image_build({})

        with github_workflow_trigger_context(trigger) as request:
            assert 'endpoint_v1_image_for_ecs_runners_post.yml' in request.full_url

    def test_uses_main_branch(self, github_workflow_trigger_context):
        """Test that main branch is used."""
        def trigger():
            handler.trigger_ecs_image_build({})

        with github_workflow_trigger_context(trigger) as request:
            assert b'"ref": "main"' in request.data
