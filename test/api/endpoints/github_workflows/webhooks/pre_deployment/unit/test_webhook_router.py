"""Unit tests for webhook_router Lambda."""
import base64
import hashlib
import hmac
import json
import urllib.error
from contextlib import contextmanager
from typing import Any, Iterator
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from .conftest import load_lambda_module, run_async


def _compute_signature(body: str, secret: str) -> str:
    """Compute GitHub webhook signature."""
    return hmac.new(
        secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def _create_mock_sqs_with_error() -> MagicMock:
    """Create a mock SQS client that raises ClientError on send_message."""
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
    async def mock_check(*_args, **_kwargs):
        return is_duplicate
    with patch.object(router_module, 'check_and_record_idempotency', side_effect=mock_check):
        with patch.object(router_module, 'publish_metric'):
            yield


@pytest.fixture(name="router_module")
def router_module_fixture():
    """Load webhook_router module for testing."""
    env_vars = {
        'WEBHOOK_SECRET_NAME': '/test/webhook-secret',
        'IDEMPOTENCY_TABLE_NAME': 'test-idempotency-table',
        'IGNORED_EVENTS_QUEUE_URL': 'https://sqs.us-east-2.amazonaws.com/123456789/ignored-queue',
        'ARCHIVE_BUCKET_NAME': 'test-archive-bucket',
    }
    with patch.dict('os.environ', env_vars):
        with patch('common.aws_clients.get_dynamodb_client'):
            with patch('common.aws_clients.get_sqs_client'):
                with patch('common.aws_clients.get_ssm_client'):
                    module = load_lambda_module(
                        "webhook_router.py", "webhook_router"
                    )
                    # Reset cache between tests
                    module.cache["webhook_secret"] = None
                    module.cache["test_mode"] = False
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
    """Tests for set_test_mode function."""

    def test_enables_test_mode(self, router_module):
        """Test that test mode can be enabled."""
        router_module.set_test_mode(True)
        assert router_module.cache["test_mode"] is True

    def test_disables_test_mode(self, router_module):
        """Test that test mode can be disabled."""
        router_module.set_test_mode(True)
        router_module.set_test_mode(False)
        assert router_module.cache["test_mode"] is False


class TestPublishMetric:
    """Tests for publish_metric function."""

    def test_publishes_metric_when_not_in_test_mode(self, router_module):
        """Test that metric is published when not in test mode."""
        router_module.cache["test_mode"] = False
        with patch.object(router_module, 'common_publish_metric') as mock_pub:
            router_module.publish_metric("TestMetric", 1.0, "Count")
            assert mock_pub.call_count == 1

    def test_skips_metric_when_in_test_mode(self, router_module):
        """Test that metric is skipped when in test mode."""
        router_module.cache["test_mode"] = True
        with patch.object(router_module, 'common_publish_metric') as mock_pub:
            router_module.publish_metric("TestMetric", 1.0, "Count")
            assert mock_pub.call_count == 0


class TestVerifySignature:
    """Tests for verify_signature function."""

    def test_returns_true_for_valid_signature(self, router_module):
        """Test that valid signature returns True."""
        body = '{"test": "data"}'
        secret = "test-secret"
        signature = f"sha256={_compute_signature(body, secret)}"
        result = router_module.verify_signature(body, signature, secret)
        assert result is True

    def test_returns_false_for_invalid_signature(self, router_module):
        """Test that invalid signature returns False."""
        body = '{"test": "data"}'
        secret = "test-secret"
        signature = "sha256=invalidsignature"
        result = router_module.verify_signature(body, signature, secret)
        assert result is False

    def test_returns_false_for_empty_signature_header(self, router_module):
        """Test that empty signature header returns False."""
        result = router_module.verify_signature("body", "", "secret")
        assert result is False

    def test_returns_false_for_malformed_signature_header(self, router_module):
        """Test that malformed signature header returns False."""
        result = router_module.verify_signature("body", "noseparator", "secret")
        assert result is False


class TestGetHeaderCaseInsensitive:
    """Tests for get_header_case_insensitive function."""

    def test_returns_value_for_exact_match(self, router_module):
        """Test that exact case match returns value."""
        headers = {"X-GitHub-Event": "workflow_job"}
        result = router_module.get_header_case_insensitive(headers, "X-GitHub-Event")
        assert result == "workflow_job"

    def test_returns_value_for_lowercase_key(self, router_module):
        """Test that lowercase key matches uppercase header."""
        headers = {"X-GITHUB-EVENT": "workflow_job"}
        result = router_module.get_header_case_insensitive(headers, "x-github-event")
        assert result == "workflow_job"

    def test_returns_none_for_missing_key(self, router_module):
        """Test that missing key returns None."""
        headers = {"X-GitHub-Event": "workflow_job"}
        result = router_module.get_header_case_insensitive(headers, "X-Missing")
        assert result is None

    def test_returns_none_for_none_headers(self, router_module):
        """Test that None headers returns None."""
        result = router_module.get_header_case_insensitive(None, "X-Test")
        assert result is None


class TestParseEventBody:
    """Tests for parse_event_body function."""

    def test_parses_json_body(self, router_module):
        """Test that JSON body is parsed correctly."""
        event = {"body": '{"action": "queued"}'}
        body_str, payload = router_module.parse_event_body(event)
        assert (body_str, payload) == ('{"action": "queued"}', {"action": "queued"})

    def test_parses_base64_encoded_body(self, router_module):
        """Test that base64 encoded body is decoded and parsed."""
        json_body = '{"action": "queued"}'
        encoded = base64.b64encode(json_body.encode()).decode()
        event = {"body": encoded, "isBase64Encoded": True}
        _body_str, payload = router_module.parse_event_body(event)
        assert payload == {"action": "queued"}

    def test_parses_url_encoded_payload(self, router_module):
        """Test that URL-encoded payload is parsed."""
        json_payload = '{"action": "queued"}'
        event = {"body": f"payload={json_payload}"}
        _body_str, payload = router_module.parse_event_body(event)
        assert payload == {"action": "queued"}

    def test_raises_value_error_for_invalid_json(self, router_module):
        """Test that ValueError is raised for invalid JSON."""
        event = {"body": "not valid json"}
        with pytest.raises(json.JSONDecodeError, match=".*"):
            router_module.parse_event_body(event)


class TestCheckAndRecordIdempotency:
    """Tests for _check_and_record_idempotency function."""

    def test_returns_false_for_new_request(self, router_module):
        """Test that new request returns False (not duplicate)."""
        mock_dynamodb = MagicMock()
        mock_dynamodb.put_item.return_value = {}
        with patch.object(router_module, 'get_dynamodb_client', return_value=mock_dynamodb):
            result = run_async(router_module.check_and_record_idempotency("new-request-id"))
            assert result is False

    def test_returns_true_for_duplicate_request(self, router_module):
        """Test that duplicate request returns True."""
        mock_dynamodb = MagicMock()
        mock_dynamodb.put_item.side_effect = ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException", "Message": "exists"}},
            "PutItem"
        )
        with patch.object(router_module, 'get_dynamodb_client', return_value=mock_dynamodb):
            result = run_async(router_module.check_and_record_idempotency("dup-request-id"))
            assert result is True

    def test_returns_false_when_table_name_not_set(self, router_module):
        """Test that missing table name returns False and skips check."""
        with patch.dict('os.environ', {'IDEMPOTENCY_TABLE_NAME': ''}):
            result = run_async(router_module.check_and_record_idempotency("any-id"))
            assert result is False

    def test_returns_false_on_other_dynamodb_errors(self, router_module):
        """Test that other DynamoDB errors return False."""
        mock_dynamodb = MagicMock()
        mock_dynamodb.put_item.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}},
            "PutItem"
        )
        with patch.object(router_module, 'get_dynamodb_client', return_value=mock_dynamodb):
            result = run_async(router_module.check_and_record_idempotency("request-id"))
            assert result is False


class TestArchiveIgnoredEvent:
    """Tests for archive_ignored_event function."""

    def test_returns_success_on_archive(self, router_module):
        """Test that successful archive returns success."""
        with patch.object(router_module, 'put_json_to_s3'):
            result = router_module.archive_ignored_event({"test": "data"}, "test reason")
            assert result["success"] is True and "ignored-events/" in result["key"]

    def test_returns_error_when_bucket_not_set(self, router_module):
        """Test that missing bucket returns error."""
        with patch.dict('os.environ', {'ARCHIVE_BUCKET_NAME': ''}):
            result = router_module.archive_ignored_event({"test": "data"}, "reason")
            assert result["success"] is False

    def test_returns_error_on_s3_failure(self, router_module):
        """Test that S3 failure returns error."""
        s3_error = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}},
            "PutObject"
        )
        with patch.object(router_module, 'put_json_to_s3', side_effect=s3_error):
            result = router_module.archive_ignored_event({"test": "data"}, "reason")
            assert result["success"] is False


class TestHandleWorkflowRun:
    """Tests for handle_workflow_run function."""

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
        result = router_module.handle_workflow_run(event_data)
        body = json.loads(result["body"])
        assert result["statusCode"] == 200 and body["run_id"] == 12345

    def test_includes_action_in_response(self, router_module):
        """Test that action is included in response message."""
        event_data = {
            "action": "requested",
            "workflow_run": {"id": 123, "name": "Test", "conclusion": None}
        }
        result = router_module.handle_workflow_run(event_data)
        body = json.loads(result["body"])
        assert "requested" in body["message"]


class TestGetWebhookSecret:
    """Tests for get_webhook_secret function."""

    def test_returns_cached_secret(self, router_module):
        """Test that cached secret is returned."""
        router_module.cache["webhook_secret"] = "cached-secret"
        result = run_async(router_module.get_webhook_secret())
        assert result == "cached-secret"

    def test_retrieves_secret_from_ssm(self, router_module):
        """Test that secret is retrieved from SSM when not cached."""
        router_module.cache["webhook_secret"] = None
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "ssm-secret"}}
        with patch.object(router_module, 'get_ssm_client', return_value=mock_ssm):
            result = run_async(router_module.get_webhook_secret())
            assert result == "ssm-secret"

    def test_force_refresh_clears_cache(self, router_module):
        """Test that force_refresh clears cache before retrieval."""
        router_module.cache["webhook_secret"] = "old-secret"
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "new-secret"}}
        with patch.object(router_module, 'get_ssm_client', return_value=mock_ssm):
            result = run_async(router_module.get_webhook_secret(force_refresh=True))
            assert result == "new-secret"

    def test_raises_runtime_error_on_ssm_error(self, router_module):
        """Test that RuntimeError is raised on SSM error."""
        router_module.cache["webhook_secret"] = None
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}},
            "GetParameter"
        )
        with patch.object(router_module, 'get_ssm_client', return_value=mock_ssm):
            with pytest.raises(RuntimeError, match=".*"):
                run_async(router_module.get_webhook_secret())


class TestVerifyWebhookSignature:
    """Tests for verify_webhook_signature function."""

    def test_returns_empty_dict_on_valid_signature(self, router_module):
        """Test that valid signature returns empty dict (no error)."""
        body = '{"test": "data"}'
        secret = "test-secret"
        signature = f"sha256={_compute_signature(body, secret)}"
        async def mock_get_secret(*_args, **_kwargs):
            return secret
        with patch.object(router_module, 'get_webhook_secret', side_effect=mock_get_secret):
            result = run_async(router_module.verify_webhook_signature(body, signature))
            assert result == {}

    def test_returns_401_on_invalid_signature(self, router_module):
        """Test that invalid signature returns 401."""
        async def mock_get_secret(*_args, **_kwargs):
            return "secret"
        with patch.object(router_module, 'get_webhook_secret', side_effect=mock_get_secret):
            result = run_async(router_module.verify_webhook_signature("body", "sha256=invalid"))
            assert result["statusCode"] == 401

    def test_returns_500_when_secret_unavailable(self, router_module):
        """Test that unavailable secret returns 500."""
        async def mock_get_secret(*_args, **_kwargs):
            raise RuntimeError("No secret")
        with patch.object(router_module, 'get_webhook_secret', side_effect=mock_get_secret):
            result = run_async(router_module.verify_webhook_signature("body", "sha256=sig"))
            assert result["statusCode"] == 500


class TestProcessWebhookEvent:
    """Tests for process_webhook_event function."""

    def test_returns_400_for_invalid_json(self, router_module):
        """Test that invalid JSON returns 400."""
        event = {"body": "not json"}
        result = run_async(router_module.process_webhook_event(event, {}, 0))
        assert result["statusCode"] == 400

    def test_returns_200_for_ping_event(self, router_module):
        """Test that ping event returns 200 with pong."""
        event = {"body": '{"zen": "test"}'}
        headers = {"x-github-event": "ping"}
        with patch.object(router_module, 'publish_metric'):
            result = run_async(router_module.process_webhook_event(event, headers, 0))
            body = json.loads(result["body"])
            assert result["statusCode"] == 200 and body["message"] == "pong"

    def test_returns_200_for_duplicate_delivery(self, router_module):
        """Test that duplicate delivery returns 200."""
        event = {"body": '{"action": "queued"}'}
        headers = {"x-github-delivery": "dup-123", "x-github-event": "workflow_job"}
        with _mock_idempotency_check(router_module, is_duplicate=True):
            result = run_async(router_module.process_webhook_event(event, headers, 0))
            body = json.loads(result["body"])
            assert result["statusCode"] == 200 and "Duplicate" in body["message"]

    def test_returns_error_on_signature_verification_failure(self, router_module):
        """Test that signature verification failure returns error."""
        event = {"body": '{"action": "queued"}'}
        headers = {"x-github-event": "workflow_job", "x-hub-signature-256": "sha256=invalid"}
        async def mock_verify(*_args, **_kwargs):
            return {"statusCode": 401, "body": "Invalid signature"}
        with patch.object(router_module, 'verify_webhook_signature', side_effect=mock_verify):
            result = run_async(router_module.process_webhook_event(event, headers, 0))
            assert result["statusCode"] == 401

    def test_ignores_unknown_event_type(self, router_module):
        """Test that unknown event types are ignored."""
        event = {"body": '{"action": "created"}'}
        headers = {"x-github-event": "issues", "x-github-delivery": "new-456"}
        with _mock_idempotency_check(router_module):
            result = run_async(router_module.process_webhook_event(event, headers, 0))
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
            result = run_async(router_module.process_webhook_event(event, headers, 0))
            assert result["statusCode"] == 200


class TestHandleApiGatewayEvent:
    """Tests for handle_api_gateway_event function."""

    def test_returns_cors_headers_for_options(self, router_module):
        """Test that OPTIONS request returns CORS headers."""
        event = {"httpMethod": "OPTIONS", "headers": {}}
        result = run_async(router_module.handle_api_gateway_event(event, 0))
        assert result["statusCode"] == 200 and "Access-Control-Allow-Origin" in result["headers"]

    def test_sets_test_mode_from_header(self, router_module):
        """Test that x-test-mode header enables test mode."""
        event = {
            "httpMethod": "POST",
            "headers": {"x-test-mode": "true"},
            "body": '{"action": "ping"}'
        }
        async def mock_process(*_args, **_kwargs):
            return {"statusCode": 200}
        with patch.object(router_module, 'process_webhook_event', side_effect=mock_process):
            run_async(router_module.handle_api_gateway_event(event, 0))
            assert router_module.cache["test_mode"] is True

    def test_extracts_method_from_request_context(self, router_module):
        """Test that method is extracted from requestContext for HTTP API."""
        event = {
            "headers": {},
            "requestContext": {"http": {"method": "OPTIONS"}},
            "body": ""
        }
        result = run_async(router_module.handle_api_gateway_event(event, 0))
        assert result["statusCode"] == 200 and "Access-Control-Allow-Origin" in result["headers"]


class TestAsyncHandler:
    """Tests for async_handler function."""

    def test_handles_api_gateway_event(self, router_module):
        """Test that API Gateway event is handled."""
        event = {"httpMethod": "OPTIONS", "headers": {}}
        result = run_async(router_module.async_handler(event))
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
        async def mock_handle(*_args, **_kwargs):
            return {"success": True}
        mock_ingress.handle = mock_handle
        with patch.object(router_module, 'get_ingress_handler', return_value=mock_ingress):
            result = run_async(router_module.async_handler(event))
            assert result["statusCode"] == 200

    def test_raises_on_sqs_failure(self, router_module):
        """Test that SQS failure raises RuntimeError."""
        sqs_record = {
            "eventSource": "aws:sqs",
            "body": "{}"
        }
        event = {"Records": [sqs_record]}
        mock_ingress = MagicMock()
        async def mock_handle(*_args, **_kwargs):
            return {"success": False}
        mock_ingress.handle = mock_handle
        with patch.object(router_module, 'get_ingress_handler', return_value=mock_ingress):
            with pytest.raises(RuntimeError, match=".*"):
                run_async(router_module.async_handler(event))


class TestIngressDeps:
    """Tests for IngressDeps class used by SQS event handling."""

    def test_ingress_depsget_webhook_secret(self, router_module):
        """Test IngressDeps.get_webhook_secret calls get_webhook_secret."""
        async def mock_get_secret():
            return "test-secret"
        with patch.object(router_module, 'get_webhook_secret', side_effect=mock_get_secret):
            handler = router_module.get_ingress_handler()
            deps = handler.get_deps()
            result = run_async(deps.get_webhook_secret())
            assert result == "test-secret"

    def test_ingress_deps_verify_signature(self, router_module):
        """Test IngressDeps.verify_signature calls _verify_signature."""
        with patch.object(router_module, 'verify_signature', return_value=True):
            handler = router_module.get_ingress_handler()
            deps = handler.get_deps()
            result = deps.verify_signature("body", "sig", "secret")
            assert result is True

    def test_ingress_deps_publish_metric(self, router_module):
        """Test IngressDeps.publish_metric calls _publish_metric."""
        with patch.object(router_module, 'publish_metric') as mock_metric:
            handler = router_module.get_ingress_handler()
            deps = handler.get_deps()
            deps.publish_metric("TestMetric", 1.0, "Count")
            assert mock_metric.call_count == 1

    def test_ingress_deps_check_idempotency(self, router_module):
        """Test IngressDeps.check_idempotency calls _check_and_record_idempotency."""
        async def mock_check(*_args):
            return True
        with patch.object(router_module, 'check_and_record_idempotency', side_effect=mock_check):
            handler = router_module.get_ingress_handler()
            deps = handler.get_deps()
            result = run_async(deps.check_idempotency("delivery-id"))
            assert result is True

    def test_ingress_deps_enqueue_ignored(self, router_module):
        """Test IngressDeps.enqueue_ignored calls archive_ignored_event."""
        with patch.object(router_module, 'archive_ignored_event') as mock_archive:
            handler = router_module.get_ingress_handler()
            deps = handler.get_deps()
            deps.enqueue_ignored({"payload": "data"}, "test reason")
            assert mock_archive.call_count == 1


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    def test_invokes_async_handler(self, router_module, lambda_context):
        """Test that lambda_handler invokes async handler."""
        event = {"httpMethod": "OPTIONS", "headers": {}}
        result = router_module.lambda_handler(event, lambda_context)
        assert result["statusCode"] == 200

    def test_returns_response_dict(self, router_module, lambda_context):
        """Test that lambda_handler returns a response dictionary."""
        event = {"httpMethod": "OPTIONS", "headers": {}}
        result = router_module.lambda_handler(event, lambda_context)
        assert isinstance(result, dict) and "statusCode" in result
