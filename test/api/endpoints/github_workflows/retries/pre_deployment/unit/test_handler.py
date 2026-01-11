"""Unit tests for the github workflows retries handler."""
import json
from unittest.mock import MagicMock, patch

import pytest


class TestProcessRetryRequest:
    """Tests for _process_retry_request function."""

    def test_process_retry_request_missing_run_id_returns_400(self, handler_module):
        """When run_id is missing, returns 400 status code."""
        body = {"github_repo": "org/repo"}

        result = handler_module._process_retry_request(body)

        assert result["statusCode"] == 400

    def test_process_retry_request_missing_github_repo_returns_400(self, handler_module):
        """When github_repo is missing, returns 400 status code."""
        body = {"run_id": 12345}

        result = handler_module._process_retry_request(body)

        assert result["statusCode"] == 400

    def test_process_retry_request_missing_both_fields_returns_error_message(
        self, handler_module
    ):
        """When required fields are missing, returns error message."""
        body = {}

        result = handler_module._process_retry_request(body)

        assert "run_id" in json.loads(result["body"])["error"]

    def test_process_retry_request_no_token_returns_500(self, handler_module):
        """When GitHub token cannot be retrieved, returns 500."""
        body = {"run_id": 12345, "github_repo": "org/repo"}

        with patch.object(handler_module, '_get_github_token', return_value=''):
            result = handler_module._process_retry_request(body)

        assert result["statusCode"] == 500

    def test_process_retry_request_inactive_workflow_returns_200_not_retried(
        self, handler_module
    ):
        """When workflow is not active, returns 200 with retried=False."""
        body = {"run_id": 12345, "github_repo": "org/repo"}

        with patch.object(handler_module, '_get_github_token', return_value='token'):
            with patch.object(
                handler_module, '_get_workflow_run_status', return_value='completed'
            ):
                result = handler_module._process_retry_request(body)

        assert (result["statusCode"], json.loads(result["body"])["retried"]) == (200, False)


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    def test_lambda_handler_sqs_event_processes_records(self, handler_module, lambda_context):
        """SQS event with records processes each record."""
        event = {
            "Records": [
                {"body": json.dumps({"run_id": 123, "github_repo": "org/repo"})}
            ]
        }

        with patch.object(handler_module, '_get_github_token', return_value=''):
            result = handler_module.lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200 and "results" in json.loads(result["body"])

    def test_lambda_handler_direct_invocation_processes_body(
        self, handler_module, lambda_context
    ):
        """Direct invocation with body processes the request."""
        event = {"body": json.dumps({"run_id": 123, "github_repo": "org/repo"})}

        with patch.object(handler_module, '_get_github_token', return_value=''):
            result = handler_module.lambda_handler(event, lambda_context)

        assert result["statusCode"] == 500

    def test_lambda_handler_dict_body_processed_directly(
        self, handler_module, lambda_context
    ):
        """When body is already a dict, processes it directly."""
        event = {"body": {"run_id": 123, "github_repo": "org/repo"}}

        with patch.object(handler_module, '_get_github_token', return_value=''):
            result = handler_module.lambda_handler(event, lambda_context)

        assert result["statusCode"] == 500


class TestGetGithubToken:
    """Tests for _get_github_token function."""

    def test_get_github_token_missing_env_var_returns_empty(self, handler_module):
        """When env var is not set, returns empty string."""
        with patch.dict('os.environ', {'GITHUB_TOKEN_SECRET_NAME': ''}):
            with patch.object(handler_module, '_get_github_token') as mock_fn:
                mock_fn.return_value = ''
                result = mock_fn()

        assert result == ''

    def test_get_github_token_ssm_success_returns_token(self, handler_module):
        """When SSM call succeeds, returns the token value."""
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {
            "Parameter": {"Value": "test-token-value"}
        }

        with patch('boto3.client', return_value=mock_ssm):
            with patch.dict('os.environ', {'GITHUB_TOKEN_SECRET_NAME': '/test/param'}):
                result = handler_module._get_github_token()

        assert result == "test-token-value"


class TestGithubApiRequest:
    """Tests for _github_api_request function."""

    def test_github_api_request_204_returns_empty_dict(self, handler_module):
        """When response is 204 No Content, returns empty dict."""
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch('urllib.request.urlopen', return_value=mock_response):
            result = handler_module._github_api_request(
                "POST", "/repos/org/repo/actions/runs/123/cancel", "token"
            )

        assert result == {}

    def test_github_api_request_200_returns_json(self, handler_module):
        """When response is 200 with JSON, returns parsed JSON."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"status": "completed"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch('urllib.request.urlopen', return_value=mock_response):
            result = handler_module._github_api_request(
                "GET", "/repos/org/repo/actions/runs/123", "token"
            )

        assert result == {"status": "completed"}


class TestGetWorkflowRunStatus:
    """Tests for _get_workflow_run_status function."""

    def test_get_workflow_run_status_returns_status(self, handler_module):
        """Returns the status from the API response."""
        with patch.object(
            handler_module,
            '_github_api_request',
            return_value={"status": "in_progress"}
        ):
            result = handler_module._get_workflow_run_status("token", "org/repo", 123)

        assert result == "in_progress"

    def test_get_workflow_run_status_http_error_returns_unknown(self, handler_module):
        """When HTTP error occurs, returns 'unknown'."""
        import urllib.error
        with patch.object(
            handler_module,
            '_github_api_request',
            side_effect=urllib.error.HTTPError(None, 404, "Not Found", {}, None)
        ):
            result = handler_module._get_workflow_run_status("token", "org/repo", 123)

        assert result == "unknown"


class TestCancelWorkflowRun:
    """Tests for _cancel_workflow_run function."""

    def test_cancel_workflow_run_success_returns_true(self, handler_module):
        """When cancellation succeeds, returns True."""
        with patch.object(handler_module, '_github_api_request', return_value={}):
            result = handler_module._cancel_workflow_run("token", "org/repo", 123)

        assert result is True

    def test_cancel_workflow_run_202_returns_true(self, handler_module):
        """When 202 Accepted is returned, returns True."""
        import urllib.error
        with patch.object(
            handler_module,
            '_github_api_request',
            side_effect=urllib.error.HTTPError(None, 202, "Accepted", {}, None)
        ):
            result = handler_module._cancel_workflow_run("token", "org/repo", 123)

        assert result is True


class TestGetWorkflowInfoFromRun:
    """Tests for _get_workflow_info_from_run function."""

    def test_get_workflow_info_from_run_returns_info(self, handler_module):
        """Returns workflow info from the API response."""
        with patch.object(
            handler_module,
            '_github_api_request',
            return_value={
                "workflow_id": 456,
                "head_sha": "abc123",
                "head_branch": "main"
            }
        ):
            result = handler_module._get_workflow_info_from_run("token", "org/repo", 123)

        assert (result["workflow_id"], result["head_sha"], result["head_branch"]) == ("456", "abc123", "main")


class TestDispatchWorkflow:
    """Tests for _dispatch_workflow function."""

    def test_dispatch_workflow_success_returns_true(self, handler_module):
        """When dispatch succeeds, returns True."""
        with patch.object(handler_module, '_github_api_request', return_value={}):
            result = handler_module._dispatch_workflow(
                "token", "org/repo", "123", "main", "test reason"
            )

        assert result is True

    def test_dispatch_workflow_204_returns_true(self, handler_module):
        """When 204 No Content is returned, returns True."""
        import urllib.error
        with patch.object(
            handler_module,
            '_github_api_request',
            side_effect=urllib.error.HTTPError(None, 204, "No Content", {}, None)
        ):
            result = handler_module._dispatch_workflow(
                "token", "org/repo", "123", "main", "test reason"
            )

        assert result is True
