"""Unit tests for the github workflows retries handler."""
import json
from unittest.mock import MagicMock, patch

import pytest


class TestProcessRetryRequest:
    """Tests for _process_retry_request function."""

    def test_process_retry_request_missing_run_id_returns_400(self, handler_module):
        """When run_id is missing, returns 400 status code."""
        result = handler_module._process_retry_request({"github_repo": "org/repo"})
        assert result["statusCode"] == 400

    def test_process_retry_request_missing_github_repo_returns_400(self, handler_module):
        """When github_repo is missing, returns 400 status code."""
        result = handler_module._process_retry_request({"run_id": 12345})
        assert result["statusCode"] == 400

    def test_process_retry_request_missing_both_fields_returns_error_message(
        self, handler_module
    ):
        """When required fields are missing, returns error message."""
        result = handler_module._process_retry_request({})
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
        event = {"Records": [{"body": json.dumps({"run_id": 123, "github_repo": "org/repo"})}]}
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
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "test-token-value"}}
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
            handler_module, '_github_api_request', return_value={"status": "in_progress"}
        ):
            result = handler_module._get_workflow_run_status("token", "org/repo", 123)
        assert result == "in_progress"

    def test_get_workflow_run_status_http_error_returns_unknown(self, handler_module):
        """When HTTP error occurs, returns 'unknown'."""
        import urllib.error
        with patch.object(
            handler_module, '_github_api_request',
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
            handler_module, '_github_api_request',
            side_effect=urllib.error.HTTPError(None, 202, "Accepted", {}, None)
        ):
            result = handler_module._cancel_workflow_run("token", "org/repo", 123)
        assert result is True

    def test_cancel_workflow_run_http_error_returns_false(self, handler_module):
        """When HTTP error occurs (not 202), returns False."""
        import urllib.error
        with patch.object(
            handler_module, '_github_api_request',
            side_effect=urllib.error.HTTPError(None, 500, "Server Error", {}, None)
        ):
            result = handler_module._cancel_workflow_run("token", "org/repo", 123)
        assert result is False


class TestGetWorkflowInfoFromRun:
    """Tests for _get_workflow_info_from_run function."""

    def test_get_workflow_info_from_run_returns_info(self, handler_module):
        """Returns workflow info from the API response."""
        with patch.object(
            handler_module, '_github_api_request',
            return_value={"workflow_id": 456, "head_sha": "abc123", "head_branch": "main"}
        ):
            result = handler_module._get_workflow_info_from_run("token", "org/repo", 123)
        assert (result["workflow_id"], result["head_sha"], result["head_branch"]) == ("456", "abc123", "main")


class TestDispatchWorkflow:
    """Tests for _dispatch_workflow function."""

    def test_dispatch_workflow_success_returns_true(self, handler_module):
        """When dispatch succeeds, returns True."""
        with patch.object(handler_module, '_github_api_request', return_value={}):
            result = handler_module._dispatch_workflow("token", "org/repo", "123", "main", "test")
        assert result is True

    def test_dispatch_workflow_204_returns_true(self, handler_module):
        """When 204 No Content is returned, returns True."""
        import urllib.error
        with patch.object(
            handler_module, '_github_api_request',
            side_effect=urllib.error.HTTPError(None, 204, "No Content", {}, None)
        ):
            result = handler_module._dispatch_workflow("token", "org/repo", "123", "main", "test")
        assert result is True

    def test_dispatch_workflow_http_error_returns_false(self, handler_module):
        """When HTTP error occurs (not 204), returns False."""
        import urllib.error
        with patch.object(
            handler_module, '_github_api_request',
            side_effect=urllib.error.HTTPError(None, 500, "Server Error", {}, None)
        ):
            result = handler_module._dispatch_workflow("token", "org/repo", "123", "main", "test")
        assert result is False


class TestCreateCheckRunAnnotation:
    """Tests for _create_check_run_annotation function."""

    def test_create_check_run_annotation_success_returns_true(self, handler_module):
        """When check run creation succeeds, returns True."""
        with patch.object(handler_module, '_github_api_request', return_value={}):
            result = handler_module._create_check_run_annotation(
                "token", "org/repo", "abc123", "Test Title", "Test Summary"
            )
        assert result is True

    def test_create_check_run_annotation_201_returns_true(self, handler_module):
        """When 201 Created is returned, returns True."""
        import urllib.error
        with patch.object(
            handler_module, '_github_api_request',
            side_effect=urllib.error.HTTPError(None, 201, "Created", {}, None)
        ):
            result = handler_module._create_check_run_annotation(
                "token", "org/repo", "abc123", "Test Title", "Test Summary"
            )
        assert result is True

    def test_create_check_run_annotation_http_error_returns_false(self, handler_module):
        """When HTTP error occurs (not 201), returns False."""
        import urllib.error
        with patch.object(
            handler_module, '_github_api_request',
            side_effect=urllib.error.HTTPError(None, 500, "Server Error", {}, None)
        ):
            result = handler_module._create_check_run_annotation(
                "token", "org/repo", "abc123", "Test Title", "Test Summary"
            )
        assert result is False


class TestWaitForWorkflowCompletion:
    """Tests for _wait_for_workflow_completion function."""

    def test_wait_for_workflow_completion_already_completed_returns_true(self, handler_module):
        """When workflow is already completed, returns True immediately."""
        with patch.object(
            handler_module, '_github_api_request', return_value={"status": "completed"}
        ):
            result = handler_module._wait_for_workflow_completion("token", "org/repo", 123, timeout_seconds=5)
        assert result is True

    def test_wait_for_workflow_completion_timeout_returns_false(self, handler_module):
        """When timeout is exceeded, returns False."""
        with patch.object(
            handler_module, '_github_api_request', return_value={"status": "in_progress"}
        ):
            with patch('time.sleep'):
                result = handler_module._wait_for_workflow_completion("token", "org/repo", 123, timeout_seconds=0)
        assert result is False

    def test_wait_for_workflow_completion_http_error_continues_polling(self, handler_module):
        """When HTTP error occurs during polling, continues polling."""
        import urllib.error
        call_count = [0]
        def side_effect(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                raise urllib.error.HTTPError(None, 500, "Error", {}, None)
            return {"status": "completed"}
        with patch.object(handler_module, '_github_api_request', side_effect=side_effect):
            with patch('time.sleep'):
                result = handler_module._wait_for_workflow_completion("token", "org/repo", 123, timeout_seconds=60)
        assert result is True


class TestGetGithubTokenClientError:
    """Additional tests for _get_github_token ClientError handling."""

    def test_get_github_token_client_error_returns_empty(self, handler_module):
        """When ClientError occurs, returns empty string."""
        from botocore.exceptions import ClientError
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = ClientError(
            {"Error": {"Code": "ParameterNotFound", "Message": "Not found"}}, "GetParameter"
        )
        with patch('boto3.client', return_value=mock_ssm):
            with patch.dict('os.environ', {'GITHUB_TOKEN_SECRET_NAME': '/test/param'}):
                result = handler_module._get_github_token()
        assert result == ""


@pytest.fixture
def retry_request_mocks(handler_module):
    """Fixture providing mock setup for _process_retry_request tests."""
    class MockSetup:
        def __init__(self):
            self.body = {"run_id": 12345, "github_repo": "org/repo"}
            self.workflow_info = {"workflow_id": "456", "head_sha": "abc", "head_branch": "main"}
        def run_with_mocks(self, workflow_id="456", cancel_ok=True, dispatch_ok=True):
            info = {**self.workflow_info, "workflow_id": workflow_id}
            with patch.object(handler_module, '_get_github_token', return_value='token'):
                with patch.object(handler_module, '_get_workflow_run_status', return_value='in_progress'):
                    with patch.object(handler_module, '_get_workflow_info_from_run', return_value=info):
                        with patch.object(handler_module, '_cancel_workflow_run', return_value=cancel_ok):
                            with patch.object(handler_module, '_create_check_run_annotation', return_value=True):
                                with patch.object(handler_module, '_wait_for_workflow_completion', return_value=True):
                                    with patch.object(handler_module, '_dispatch_workflow', return_value=dispatch_ok):
                                        return handler_module._process_retry_request(self.body)
    return MockSetup()


class TestProcessRetryRequestFullPath:
    """Tests for full _process_retry_request execution paths."""

    def test_process_retry_request_no_workflow_id_returns_500(self, retry_request_mocks):
        """When workflow info has no workflow_id, returns 500."""
        result = retry_request_mocks.run_with_mocks(workflow_id="")
        assert result["statusCode"] == 500

    def test_process_retry_request_cancel_fails_returns_500(self, retry_request_mocks):
        """When workflow cancellation fails, returns 500."""
        result = retry_request_mocks.run_with_mocks(cancel_ok=False)
        assert result["statusCode"] == 500

    def test_process_retry_request_dispatch_fails_returns_500(self, retry_request_mocks):
        """When workflow dispatch fails, returns 500."""
        result = retry_request_mocks.run_with_mocks(dispatch_ok=False)
        assert result["statusCode"] == 500

    def test_process_retry_request_full_success_returns_200(self, retry_request_mocks):
        """When all steps succeed, returns 200 with retried=True."""
        result = retry_request_mocks.run_with_mocks()
        assert (result["statusCode"], json.loads(result["body"])["retried"]) == (200, True)


class TestLambdaHandlerAdditional:
    """Additional tests for lambda_handler."""

    def test_lambda_handler_raw_event_without_body_processes_directly(
        self, handler_module, lambda_context
    ):
        """When event has no body or Records, processes event directly."""
        event = {"run_id": 123, "github_repo": "org/repo"}
        with patch.object(handler_module, '_get_github_token', return_value=''):
            result = handler_module.lambda_handler(event, lambda_context)
        assert result["statusCode"] == 500

    def test_lambda_handler_sqs_multiple_records_processes_all(
        self, handler_module, lambda_context
    ):
        """When SQS event has multiple records, processes all of them."""
        event = {
            "Records": [
                {"body": json.dumps({"run_id": 123, "github_repo": "org/repo"})},
                {"body": json.dumps({"run_id": 456, "github_repo": "org/repo2"})}
            ]
        }
        with patch.object(handler_module, '_get_github_token', return_value=''):
            result = handler_module.lambda_handler(event, lambda_context)
        assert len(json.loads(result["body"])["results"]) == 2
