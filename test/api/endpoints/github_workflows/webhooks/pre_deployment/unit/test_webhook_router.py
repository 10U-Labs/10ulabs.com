"""Unit tests for webhook_router Lambda."""
import base64
import hashlib
import hmac
import json
from contextlib import contextmanager
from typing import Any, Iterator
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from .conftest import load_lambda_module, run_async


def _compute_signature(body: str, secret: str) -> str:
    """Compute GitHub webhook signature."""
    return hmac.new(
        secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def _create_mock_sqs_with_error() -> MagicMock:
    """Create a mock SQS client that raises ClientError on send_message."""
    from botocore.exceptions import ClientError
    mock_sqs = MagicMock()
    mock_sqs.send_message.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "denied"}},
        "SendMessage"
    )
    return mock_sqs


def _create_queued_workflow_job_event() -> dict:
    """Create a standard queued workflow_job event for testing."""
    return {
        "action": "queued",
        "workflow_job": {
            "id": 123,
            "name": "test-job",
            "labels": ["self-hosted"],
            "status": "queued",
            "run_id": 456
        },
        "repository": {"full_name": "test/repo"}
    }


@contextmanager
def _mock_idempotency_check(router_module, is_duplicate: bool = False) -> Iterator[None]:
    """Context manager to mock idempotency check and metrics publishing."""
    async def mock_check(*args, **kwargs):
        return is_duplicate
    with patch.object(router_module, '_check_and_record_idempotency', side_effect=mock_check):
        with patch.object(router_module, '_publish_metric'):
            yield


@pytest.fixture(name="router_module")
def router_module_fixture():
    """Load webhook_router module for testing."""
    env_vars = {
        'WEBHOOK_SECRET_NAME': '/test/webhook-secret',
        'IDEMPOTENCY_TABLE_NAME': 'test-idempotency-table',
        'JOB_QUEUE_URL': 'https://sqs.us-east-2.amazonaws.com/123456789/test-queue',
        'IGNORED_EVENTS_QUEUE_URL': 'https://sqs.us-east-2.amazonaws.com/123456789/ignored-queue',
        # Note: CANCELLATION_QUEUE_URL removed - runners are ephemeral and self-terminate
        'API_BASE_URL': 'https://api.example.com',
        'API_KEY_PARAMETER_NAME': '/test/api-key',
    }
    with patch.dict('os.environ', env_vars):
        with patch('common.aws_clients.get_dynamodb_client'):
            with patch('common.aws_clients.get_sqs_client'):
                with patch('common.aws_clients.get_ssm_client'):
                    module = load_lambda_module(
                        "webhook_router.py", "webhook_router"
                    )
                    # Reset cache between tests
                    module._cache["webhook_secret"] = None
                    module._cache["api_key"] = None
                    module._cache["test_mode"] = False
                    yield module


@contextmanager
def mock_ssm_client(module: Any, secret: str = "test-secret") -> Iterator[MagicMock]:
    """Context manager for mocking SSM client."""
    mock_client = MagicMock()
    mock_client.get_parameter.return_value = {
        "Parameter": {"Value": secret}
    }
    with patch.object(module, 'get_ssm_client', return_value=mock_client):
        yield mock_client


class TestSetTestMode:
    """Tests for _set_test_mode function."""

    def test_enables_test_mode(self, router_module):
        """Test that test mode can be enabled."""
        router_module._set_test_mode(True)
        assert router_module._cache["test_mode"] is True

    def test_disables_test_mode(self, router_module):
        """Test that test mode can be disabled."""
        router_module._set_test_mode(True)
        router_module._set_test_mode(False)
        assert router_module._cache["test_mode"] is False


class TestPublishMetric:
    """Tests for _publish_metric function."""

    def test_publishes_metric_when_not_in_test_mode(self, router_module):
        """Test that metric is published when not in test mode."""
        router_module._cache["test_mode"] = False
        with patch.object(router_module, '_common_publish_metric') as mock_pub:
            router_module._publish_metric("TestMetric", 1.0, "Count")
            assert mock_pub.call_count == 1

    def test_skips_metric_when_in_test_mode(self, router_module):
        """Test that metric is skipped when in test mode."""
        router_module._cache["test_mode"] = True
        with patch.object(router_module, '_common_publish_metric') as mock_pub:
            router_module._publish_metric("TestMetric", 1.0, "Count")
            assert mock_pub.call_count == 0


class TestGetApiKey:
    """Tests for _get_api_key function."""

    def test_returns_cached_api_key(self, router_module):
        """Test that cached API key is returned without SSM call."""
        router_module._cache["api_key"] = "cached-key"
        result = router_module._get_api_key()
        assert result == "cached-key"

    def test_retrieves_api_key_from_ssm(self, router_module):
        """Test that API key is retrieved from SSM when not cached."""
        router_module._cache["api_key"] = None
        with mock_ssm_client(router_module, "ssm-api-key") as mock_ssm:
            with patch.object(router_module, 'get_ssm_client', return_value=mock_ssm):
                result = router_module._get_api_key()
                assert result == "ssm-api-key"

    def test_caches_api_key_after_retrieval(self, router_module):
        """Test that API key is cached after retrieval."""
        router_module._cache["api_key"] = None
        with mock_ssm_client(router_module, "new-api-key") as mock_ssm:
            with patch.object(router_module, 'get_ssm_client', return_value=mock_ssm):
                router_module._get_api_key()
                assert router_module._cache["api_key"] == "new-api-key"

    def test_raises_runtime_error_when_param_name_not_set(self, router_module):
        """Test that RuntimeError is raised when parameter name not set."""
        router_module._cache["api_key"] = None
        raised = False
        with patch.dict('os.environ', {'API_KEY_PARAMETER_NAME': ''}):
            with pytest.raises(RuntimeError):
                router_module._get_api_key()
            raised = True
        assert raised

    def test_raises_runtime_error_on_ssm_error(self, router_module):
        """Test that RuntimeError is raised on SSM client error."""
        from botocore.exceptions import ClientError
        router_module._cache["api_key"] = None
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "GetParameter"
        )
        raised = False
        with patch.object(router_module, 'get_ssm_client', return_value=mock_ssm):
            with pytest.raises(RuntimeError):
                router_module._get_api_key()
            raised = True
        assert raised


class TestVerifySignature:
    """Tests for _verify_signature function."""

    def test_returns_true_for_valid_signature(self, router_module):
        """Test that valid signature returns True."""
        body = '{"test": "data"}'
        secret = "test-secret"
        signature = f"sha256={_compute_signature(body, secret)}"
        result = router_module._verify_signature(body, signature, secret)
        assert result is True

    def test_returns_false_for_invalid_signature(self, router_module):
        """Test that invalid signature returns False."""
        body = '{"test": "data"}'
        secret = "test-secret"
        signature = "sha256=invalidsignature"
        result = router_module._verify_signature(body, signature, secret)
        assert result is False

    def test_returns_false_for_empty_signature_header(self, router_module):
        """Test that empty signature header returns False."""
        result = router_module._verify_signature("body", "", "secret")
        assert result is False

    def test_returns_false_for_malformed_signature_header(self, router_module):
        """Test that malformed signature header returns False."""
        result = router_module._verify_signature("body", "noseparator", "secret")
        assert result is False


class TestGetHeaderCaseInsensitive:
    """Tests for _get_header_case_insensitive function."""

    def test_returns_value_for_exact_match(self, router_module):
        """Test that exact case match returns value."""
        headers = {"X-GitHub-Event": "workflow_job"}
        result = router_module._get_header_case_insensitive(headers, "X-GitHub-Event")
        assert result == "workflow_job"

    def test_returns_value_for_lowercase_key(self, router_module):
        """Test that lowercase key matches uppercase header."""
        headers = {"X-GITHUB-EVENT": "workflow_job"}
        result = router_module._get_header_case_insensitive(headers, "x-github-event")
        assert result == "workflow_job"

    def test_returns_none_for_missing_key(self, router_module):
        """Test that missing key returns None."""
        headers = {"X-GitHub-Event": "workflow_job"}
        result = router_module._get_header_case_insensitive(headers, "X-Missing")
        assert result is None

    def test_returns_none_for_none_headers(self, router_module):
        """Test that None headers returns None."""
        result = router_module._get_header_case_insensitive(None, "X-Test")
        assert result is None


class TestParseEventBody:
    """Tests for _parse_event_body function."""

    def test_parses_json_body(self, router_module):
        """Test that JSON body is parsed correctly."""
        event = {"body": '{"action": "queued"}'}
        body_str, payload = router_module._parse_event_body(event)
        assert (body_str, payload) == ('{"action": "queued"}', {"action": "queued"})

    def test_parses_base64_encoded_body(self, router_module):
        """Test that base64 encoded body is decoded and parsed."""
        json_body = '{"action": "queued"}'
        encoded = base64.b64encode(json_body.encode()).decode()
        event = {"body": encoded, "isBase64Encoded": True}
        body_str, payload = router_module._parse_event_body(event)
        assert payload == {"action": "queued"}

    def test_parses_url_encoded_payload(self, router_module):
        """Test that URL-encoded payload is parsed."""
        json_payload = '{"action": "queued"}'
        event = {"body": f"payload={json_payload}"}
        body_str, payload = router_module._parse_event_body(event)
        assert payload == {"action": "queued"}

    def test_raises_value_error_for_invalid_json(self, router_module):
        """Test that ValueError is raised for invalid JSON."""
        event = {"body": "not valid json"}
        raised = False
        with pytest.raises(json.JSONDecodeError):
            router_module._parse_event_body(event)
        raised = True
        assert raised


class TestCheckAndRecordIdempotency:
    """Tests for _check_and_record_idempotency function."""

    def test_returns_false_for_new_request(self, router_module):
        """Test that new request returns False (not duplicate)."""
        mock_dynamodb = MagicMock()
        mock_dynamodb.put_item.return_value = {}
        with patch.object(router_module, 'get_dynamodb_client', return_value=mock_dynamodb):
            result = run_async(router_module._check_and_record_idempotency("new-request-id"))
            assert result is False

    def test_returns_true_for_duplicate_request(self, router_module):
        """Test that duplicate request returns True."""
        from botocore.exceptions import ClientError
        mock_dynamodb = MagicMock()
        mock_dynamodb.put_item.side_effect = ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException", "Message": "exists"}},
            "PutItem"
        )
        with patch.object(router_module, 'get_dynamodb_client', return_value=mock_dynamodb):
            result = run_async(router_module._check_and_record_idempotency("dup-request-id"))
            assert result is True

    def test_returns_false_when_table_name_not_set(self, router_module):
        """Test that missing table name returns False and skips check."""
        with patch.dict('os.environ', {'IDEMPOTENCY_TABLE_NAME': ''}):
            result = run_async(router_module._check_and_record_idempotency("any-id"))
            assert result is False

    def test_returns_false_on_other_dynamodb_errors(self, router_module):
        """Test that other DynamoDB errors return False."""
        from botocore.exceptions import ClientError
        mock_dynamodb = MagicMock()
        mock_dynamodb.put_item.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}},
            "PutItem"
        )
        with patch.object(router_module, 'get_dynamodb_client', return_value=mock_dynamodb):
            result = run_async(router_module._check_and_record_idempotency("request-id"))
            assert result is False


class TestEnqueueJob:
    """Tests for _enqueue_job function."""

    def test_returns_success_on_send(self, router_module):
        """Test that successful send returns success."""
        mock_sqs = MagicMock()
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}
        mock_sqs.get_queue_attributes.return_value = {
            "Attributes": {"ApproximateNumberOfMessages": "5"}
        }
        with patch.object(router_module, 'get_sqs_client', return_value=mock_sqs):
            with patch.object(router_module, '_publish_metric'):
                result = run_async(router_module._enqueue_job({"job_id": 123}))
                assert result["success"] is True and result["message_id"] == "msg-123"

    def test_returns_error_when_queue_url_not_set(self, router_module):
        """Test that missing queue URL returns error."""
        with patch.dict('os.environ', {'JOB_QUEUE_URL': ''}):
            result = run_async(router_module._enqueue_job({"job_id": 123}))
            assert result["success"] is False and "not configured" in result["error"]

    def test_returns_error_on_sqs_failure(self, router_module):
        """Test that SQS failure returns error."""
        mock_sqs = _create_mock_sqs_with_error()
        with patch.object(router_module, 'get_sqs_client', return_value=mock_sqs):
            result = run_async(router_module._enqueue_job({"job_id": 123}))
            assert result["success"] is False


class TestEnqueueIgnoredEvent:
    """Tests for _enqueue_ignored_event function."""

    def test_returns_success_on_send(self, router_module):
        """Test that successful send returns success."""
        mock_sqs = MagicMock()
        mock_sqs.send_message.return_value = {"MessageId": "ignored-123"}
        with patch.object(router_module, 'get_sqs_client', return_value=mock_sqs):
            result = router_module._enqueue_ignored_event({"test": "data"}, "test reason")
            assert result["success"] is True and result["message_id"] == "ignored-123"

    def test_returns_error_when_queue_url_not_set(self, router_module):
        """Test that missing queue URL returns error."""
        with patch.dict('os.environ', {'IGNORED_EVENTS_QUEUE_URL': ''}):
            result = router_module._enqueue_ignored_event({"test": "data"}, "reason")
            assert result["success"] is False

    def test_returns_error_on_sqs_failure(self, router_module):
        """Test that SQS failure returns error."""
        mock_sqs = _create_mock_sqs_with_error()
        with patch.object(router_module, 'get_sqs_client', return_value=mock_sqs):
            result = router_module._enqueue_ignored_event({"test": "data"}, "reason")
            assert result["success"] is False


# Note: TestEnqueueCancellation removed - runners are ephemeral and self-terminate


class TestHandleWorkflowRun:
    """Tests for _handle_workflow_run function."""

    def test_returns_200_for_completed_workflow(self, router_module):
        """Test that completed workflow returns 200."""
        event_data = {
            "action": "completed",
            "workflow_run": {
                "id": 12345,
                "name": "CI",
                "conclusion": "success"
            }
        }
        result = router_module._handle_workflow_run(event_data)
        body = json.loads(result["body"])
        assert result["statusCode"] == 200 and body["run_id"] == 12345

    def test_includes_action_in_response(self, router_module):
        """Test that action is included in response message."""
        event_data = {
            "action": "requested",
            "workflow_run": {"id": 123, "name": "Test", "conclusion": None}
        }
        result = router_module._handle_workflow_run(event_data)
        body = json.loads(result["body"])
        assert "requested" in body["message"]


class TestHandleWorkflowJob:
    """Tests for _handle_workflow_job function."""

    def test_ignores_non_queued_action(self, router_module):
        """Test that non-queued action is ignored."""
        event_data = {
            "action": "completed",
            "workflow_job": {"id": 123, "name": "test", "labels": [], "status": "completed"},
            "repository": {"full_name": "test/repo"}
        }
        result = run_async(router_module._handle_workflow_job(event_data))
        body = json.loads(result["body"])
        assert result["statusCode"] == 200 and "Ignored action" in body["message"]

    def test_returns_test_mode_response_when_enabled(self, router_module):
        """Test that test mode returns test response without forwarding."""
        router_module._cache["test_mode"] = True
        event_data = {
            "action": "queued",
            "workflow_job": {
                "id": 123,
                "name": "test-job",
                "labels": ["self-hosted"],
                "status": "queued",
                "run_id": 456
            },
            "repository": {"full_name": "test/repo"}
        }
        result = run_async(router_module._handle_workflow_job(event_data))
        body = json.loads(result["body"])
        assert result["statusCode"] == 200 and body["test_mode"] is True

    def test_forwards_queued_job_to_runners(self, router_module):
        """Test that queued job is forwarded to /v1/runners."""
        router_module._cache["test_mode"] = False
        event_data = _create_queued_workflow_job_event()
        async def mock_post(*args, **kwargs):
            return {"success": True}
        with patch.object(router_module, '_post_to_runners', side_effect=mock_post):
            result = run_async(router_module._handle_workflow_job(event_data))
            body = json.loads(result["body"])
            assert result["statusCode"] == 200 and "forwarded" in body["message"].lower()

    def test_returns_500_when_forward_fails(self, router_module):
        """Test that failed forward returns 500."""
        router_module._cache["test_mode"] = False
        event_data = _create_queued_workflow_job_event()
        async def mock_post(*args, **kwargs):
            return {"success": False, "error": "Network error"}
        with patch.object(router_module, '_post_to_runners', side_effect=mock_post):
            result = run_async(router_module._handle_workflow_job(event_data))
            assert result["statusCode"] == 500


class TestPostToRunners:
    """Tests for _post_to_runners function."""

    def test_returns_error_when_api_base_url_not_set(self, router_module):
        """Test that missing API base URL returns error."""
        with patch.dict('os.environ', {'API_BASE_URL': ''}):
            result = run_async(router_module._post_to_runners({"job_id": 123}))
            assert result["success"] is False and "not configured" in result["error"]

    def test_returns_error_when_api_key_unavailable(self, router_module):
        """Test that unavailable API key returns error."""
        with patch.object(router_module, '_get_api_key', side_effect=RuntimeError("No key")):
            result = run_async(router_module._post_to_runners({"job_id": 123}))
            assert result["success"] is False

    def test_returns_success_on_successful_post(self, router_module):
        """Test that successful POST returns success."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        with patch.object(router_module, '_get_api_key', return_value="test-key"):
            with patch('urllib.request.urlopen', return_value=mock_response):
                result = run_async(router_module._post_to_runners({"job_id": 123}))
                assert result["success"] is True and result["status_code"] == 200

    def test_returns_error_on_http_error(self, router_module):
        """Test that HTTP error returns error."""
        import urllib.error
        with patch.object(router_module, '_get_api_key', return_value="test-key"):
            with patch('urllib.request.urlopen', side_effect=urllib.error.HTTPError(
                url="", code=500, msg="Internal Server Error", hdrs={}, fp=None
            )):
                result = run_async(router_module._post_to_runners({"job_id": 123}))
                assert result["success"] is False and result["status_code"] == 500

    def test_returns_error_on_url_error(self, router_module):
        """Test that URL error returns error."""
        import urllib.error
        url_err = urllib.error.URLError("Network error")
        with patch.object(router_module, '_get_api_key', return_value="test-key"):
            with patch('urllib.request.urlopen', side_effect=url_err):
                result = run_async(router_module._post_to_runners({"job_id": 123}))
                assert result["success"] is False


class TestGetWebhookSecret:
    """Tests for _get_webhook_secret function."""

    def test_returns_cached_secret(self, router_module):
        """Test that cached secret is returned."""
        router_module._cache["webhook_secret"] = "cached-secret"
        result = run_async(router_module._get_webhook_secret())
        assert result == "cached-secret"

    def test_retrieves_secret_from_ssm(self, router_module):
        """Test that secret is retrieved from SSM when not cached."""
        router_module._cache["webhook_secret"] = None
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "ssm-secret"}}
        with patch.object(router_module, 'get_ssm_client', return_value=mock_ssm):
            result = run_async(router_module._get_webhook_secret())
            assert result == "ssm-secret"

    def test_force_refresh_clears_cache(self, router_module):
        """Test that force_refresh clears cache before retrieval."""
        router_module._cache["webhook_secret"] = "old-secret"
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "new-secret"}}
        with patch.object(router_module, 'get_ssm_client', return_value=mock_ssm):
            result = run_async(router_module._get_webhook_secret(force_refresh=True))
            assert result == "new-secret"

    def test_raises_runtime_error_on_ssm_error(self, router_module):
        """Test that RuntimeError is raised on SSM error."""
        from botocore.exceptions import ClientError
        router_module._cache["webhook_secret"] = None
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}},
            "GetParameter"
        )
        raised = False
        with patch.object(router_module, 'get_ssm_client', return_value=mock_ssm):
            with pytest.raises(RuntimeError):
                run_async(router_module._get_webhook_secret())
            raised = True
        assert raised


class TestVerifyWebhookSignature:
    """Tests for _verify_webhook_signature function."""

    def test_returns_empty_dict_on_valid_signature(self, router_module):
        """Test that valid signature returns empty dict (no error)."""
        body = '{"test": "data"}'
        secret = "test-secret"
        signature = f"sha256={_compute_signature(body, secret)}"
        async def mock_get_secret(*args, **kwargs):
            return secret
        with patch.object(router_module, '_get_webhook_secret', side_effect=mock_get_secret):
            result = run_async(router_module._verify_webhook_signature(body, signature))
            assert result == {}

    def test_returns_401_on_invalid_signature(self, router_module):
        """Test that invalid signature returns 401."""
        async def mock_get_secret(*args, **kwargs):
            return "secret"
        with patch.object(router_module, '_get_webhook_secret', side_effect=mock_get_secret):
            result = run_async(router_module._verify_webhook_signature("body", "sha256=invalid"))
            assert result["statusCode"] == 401

    def test_returns_500_when_secret_unavailable(self, router_module):
        """Test that unavailable secret returns 500."""
        async def mock_get_secret(*args, **kwargs):
            raise RuntimeError("No secret")
        with patch.object(router_module, '_get_webhook_secret', side_effect=mock_get_secret):
            result = run_async(router_module._verify_webhook_signature("body", "sha256=sig"))
            assert result["statusCode"] == 500


class TestProcessWebhookEvent:
    """Tests for _process_webhook_event function."""

    def test_returns_400_for_invalid_json(self, router_module):
        """Test that invalid JSON returns 400."""
        event = {"body": "not json"}
        result = run_async(router_module._process_webhook_event(event, {}, 0))
        assert result["statusCode"] == 400

    def test_returns_200_for_ping_event(self, router_module):
        """Test that ping event returns 200 with pong."""
        event = {"body": '{"zen": "test"}'}
        headers = {"x-github-event": "ping"}
        with patch.object(router_module, '_publish_metric'):
            result = run_async(router_module._process_webhook_event(event, headers, 0))
            body = json.loads(result["body"])
            assert result["statusCode"] == 200 and body["message"] == "pong"

    def test_returns_200_for_duplicate_delivery(self, router_module):
        """Test that duplicate delivery returns 200."""
        event = {"body": '{"action": "queued"}'}
        headers = {"x-github-delivery": "dup-123", "x-github-event": "workflow_job"}
        with _mock_idempotency_check(router_module, is_duplicate=True):
            result = run_async(router_module._process_webhook_event(event, headers, 0))
            body = json.loads(result["body"])
            assert result["statusCode"] == 200 and "Duplicate" in body["message"]

    def test_handles_workflow_job_event(self, router_module):
        """Test that workflow_job event is handled."""
        event = {"body": json.dumps({
            "action": "completed",
            "workflow_job": {"id": 123, "name": "test", "labels": [], "status": "completed"},
            "repository": {"full_name": "test/repo"}
        })}
        headers = {"x-github-event": "workflow_job", "x-github-delivery": "new-123"}
        with _mock_idempotency_check(router_module):
            result = run_async(router_module._process_webhook_event(event, headers, 0))
            assert result["statusCode"] == 200

    def test_returns_error_on_signature_verification_failure(self, router_module):
        """Test that signature verification failure returns error."""
        event = {"body": '{"action": "queued"}'}
        headers = {"x-github-event": "workflow_job", "x-hub-signature-256": "sha256=invalid"}
        async def mock_verify(*args, **kwargs):
            return {"statusCode": 401, "body": "Invalid signature"}
        with patch.object(router_module, '_verify_webhook_signature', side_effect=mock_verify):
            result = run_async(router_module._process_webhook_event(event, headers, 0))
            assert result["statusCode"] == 401

    def test_ignores_unknown_event_type(self, router_module):
        """Test that unknown event types are ignored."""
        event = {"body": '{"action": "created"}'}
        headers = {"x-github-event": "issues", "x-github-delivery": "new-456"}
        with _mock_idempotency_check(router_module):
            result = run_async(router_module._process_webhook_event(event, headers, 0))
            body = json.loads(result["body"])
            assert result["statusCode"] == 200 and "ignored" in body["message"].lower()

    def test_handles_workflow_run_event(self, router_module):
        """Test that workflow_run event is handled."""
        event = {"body": json.dumps({
            "action": "completed",
            "workflow_run": {"id": 123, "name": "CI", "conclusion": "success"}
        })}
        headers = {"x-github-event": "workflow_run", "x-github-delivery": "new-456"}
        with _mock_idempotency_check(router_module):
            result = run_async(router_module._process_webhook_event(event, headers, 0))
            assert result["statusCode"] == 200


class TestHandleApiGatewayEvent:
    """Tests for _handle_api_gateway_event function."""

    def test_returns_cors_headers_for_options(self, router_module):
        """Test that OPTIONS request returns CORS headers."""
        event = {"httpMethod": "OPTIONS", "headers": {}}
        result = run_async(router_module._handle_api_gateway_event(event, 0))
        assert result["statusCode"] == 200 and "Access-Control-Allow-Origin" in result["headers"]

    def test_sets_test_mode_from_header(self, router_module):
        """Test that x-test-mode header enables test mode."""
        event = {
            "httpMethod": "POST",
            "headers": {"x-test-mode": "true"},
            "body": '{"action": "ping"}'
        }
        async def mock_process(*args, **kwargs):
            return {"statusCode": 200}
        with patch.object(router_module, '_process_webhook_event', side_effect=mock_process):
            run_async(router_module._handle_api_gateway_event(event, 0))
            assert router_module._cache["test_mode"] is True

    def test_extracts_method_from_request_context(self, router_module):
        """Test that method is extracted from requestContext for HTTP API."""
        event = {
            "headers": {},
            "requestContext": {"http": {"method": "OPTIONS"}},
            "body": ""
        }
        result = run_async(router_module._handle_api_gateway_event(event, 0))
        assert result["statusCode"] == 200 and "Access-Control-Allow-Origin" in result["headers"]


class TestAsyncHandler:
    """Tests for _async_handler function."""

    def test_handles_api_gateway_event(self, router_module):
        """Test that API Gateway event is handled."""
        event = {"httpMethod": "OPTIONS", "headers": {}}
        result = run_async(router_module._async_handler(event))
        assert result["statusCode"] == 200

    def test_handles_sqs_event(self, router_module):
        """Test that SQS event is handled."""
        sqs_record = {
            "eventSource": "aws:sqs",
            "body": json.dumps({
                "body": '{"action": "queued"}',
                "headers": {"x-github-event": "ping"}
            })
        }
        event = {"Records": [sqs_record]}
        mock_ingress = MagicMock()
        async def mock_handle(*args, **kwargs):
            return {"success": True}
        mock_ingress.handle = mock_handle
        with patch.object(router_module, '_get_ingress_handler', return_value=mock_ingress):
            result = run_async(router_module._async_handler(event))
            assert result["statusCode"] == 200

    def test_raises_on_sqs_failure(self, router_module):
        """Test that SQS failure raises RuntimeError."""
        sqs_record = {
            "eventSource": "aws:sqs",
            "body": "{}"
        }
        event = {"Records": [sqs_record]}
        mock_ingress = MagicMock()
        async def mock_handle(*args, **kwargs):
            return {"success": False}
        mock_ingress.handle = mock_handle
        raised = False
        with patch.object(router_module, '_get_ingress_handler', return_value=mock_ingress):
            with pytest.raises(RuntimeError):
                run_async(router_module._async_handler(event))
            raised = True
        assert raised


class TestIngressDeps:
    """Tests for IngressDeps class used by SQS event handling."""

    def test_ingress_deps_get_webhook_secret(self, router_module):
        """Test IngressDeps.get_webhook_secret calls _get_webhook_secret."""
        async def mock_get_secret():
            return "test-secret"
        with patch.object(router_module, '_get_webhook_secret', side_effect=mock_get_secret):
            handler = router_module._get_ingress_handler()
            deps = handler.get_deps()
            result = run_async(deps.get_webhook_secret())
            assert result == "test-secret"

    def test_ingress_deps_verify_signature(self, router_module):
        """Test IngressDeps.verify_signature calls _verify_signature."""
        with patch.object(router_module, '_verify_signature', return_value=True):
            handler = router_module._get_ingress_handler()
            deps = handler.get_deps()
            result = deps.verify_signature("body", "sig", "secret")
            assert result is True

    def test_ingress_deps_publish_metric(self, router_module):
        """Test IngressDeps.publish_metric calls _publish_metric."""
        with patch.object(router_module, '_publish_metric') as mock_metric:
            handler = router_module._get_ingress_handler()
            deps = handler.get_deps()
            deps.publish_metric("TestMetric", 1.0, "Count")
            assert mock_metric.call_count == 1

    def test_ingress_deps_check_idempotency(self, router_module):
        """Test IngressDeps.check_idempotency calls _check_and_record_idempotency."""
        async def mock_check(*args):
            return True
        with patch.object(router_module, '_check_and_record_idempotency', side_effect=mock_check):
            handler = router_module._get_ingress_handler()
            deps = handler.get_deps()
            result = run_async(deps.check_idempotency("delivery-id"))
            assert result is True

    def test_ingress_deps_get_runner_type(self, router_module):
        """Test IngressDeps.get_runner_type returns forwarded placeholder."""
        handler = router_module._get_ingress_handler()
        deps = handler.get_deps()
        result = deps.get_runner_type(["self-hosted"])
        assert result == ("forwarded", "runners")

    def test_ingress_deps_enqueue_job(self, router_module):
        """Test IngressDeps.enqueue_job calls _post_to_runners."""
        async def mock_post(*args, **kwargs):
            return {"success": True}
        with patch.object(router_module, '_post_to_runners', side_effect=mock_post):
            handler = router_module._get_ingress_handler()
            deps = handler.get_deps()
            result = run_async(deps.enqueue_job({"job": "data"}))
            assert result["success"] is True

    # Note: test_ingress_deps_enqueue_cancellation removed - runners are ephemeral

    def test_ingress_deps_enqueue_ignored(self, router_module):
        """Test IngressDeps.enqueue_ignored calls _enqueue_ignored_event."""
        with patch.object(router_module, '_enqueue_ignored_event') as mock_enqueue:
            handler = router_module._get_ingress_handler()
            deps = handler.get_deps()
            deps.enqueue_ignored({"payload": "data"}, "test reason")
            assert mock_enqueue.call_count == 1


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    def test_invokes_async_handler(self, router_module, lambda_context):
        """Test that lambda_handler invokes async handler."""
        event = {"httpMethod": "OPTIONS", "headers": {}}
        result = router_module.lambda_handler(event, lambda_context)
        assert result["statusCode"] == 200
