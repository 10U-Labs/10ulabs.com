"""Unit tests for webhook_ingress module."""

import asyncio
import json
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from .conftest import load_lambda_module


def _run_async(coro):
    """Run an async coroutine synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _create_message_attrs(
    event_type: str = "workflow_job",
    signature: Optional[str] = "sha256=abc",
    delivery_id: Optional[str] = "delivery-123"
) -> Dict[str, Any]:
    """Create SQS message attributes for testing.

    Args:
        event_type: The GitHub event type.
        signature: The webhook signature (None to omit).
        delivery_id: The delivery ID (None to omit).

    Returns:
        Dict representing SQS message attributes.
    """
    attrs: Dict[str, Any] = {"x-github-event": {"stringValue": event_type}}
    if signature is not None:
        attrs["x-hub-signature-256"] = {"stringValue": signature}
    if delivery_id is not None:
        attrs["x-github-delivery"] = {"stringValue": delivery_id}
    return attrs


def _create_sqs_record(
    body: Dict[str, Any],
    event_type: str = "workflow_job",
    signature: Optional[str] = "sha256=abc",
    delivery_id: Optional[str] = "delivery-123"
) -> Dict[str, Any]:
    """Create an SQS record for testing webhook ingress.

    Args:
        body: The webhook event body as a dict (will be JSON-encoded).
        event_type: The GitHub event type.
        signature: The webhook signature (None to omit).
        delivery_id: The delivery ID (None to omit).

    Returns:
        Dict representing an SQS record.
    """
    attrs = _create_message_attrs(event_type, signature, delivery_id)
    return {"body": json.dumps(body), "messageAttributes": attrs}


@pytest.fixture(name="webhook_ingress_module")
def webhook_ingress_module_fixture():
    """Load webhook_ingress module for testing."""
    module = load_lambda_module("common/webhook_ingress.py", "webhook_ingress")
    yield module


@pytest.fixture(name="mock_ingress_deps")
def mock_ingress_deps_fixture():
    """Create mock dependencies for IngressHandler."""
    deps = MagicMock()
    deps.get_webhook_secret = AsyncMock(return_value="test-secret")
    deps.verify_signature = MagicMock(return_value=True)
    deps.publish_metric = MagicMock()
    deps.check_idempotency = AsyncMock(return_value=False)
    deps.get_runner_type = MagicMock(return_value=("ec2", "m5.large"))
    deps.enqueue_job = AsyncMock(return_value={"success": True})
    deps.enqueue_ignored = MagicMock()
    return deps


class TestGetMessageAttribute:
    """Tests for get_message_attribute function."""

    def test_returns_string_value_when_present(self, webhook_ingress_module):
        """Test that string value is returned when attribute exists."""
        record = {
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"}
            }
        }
        result = webhook_ingress_module.get_message_attribute(record, "x-github-event")
        assert result == "workflow_job"

    def test_returns_none_when_attribute_missing(self, webhook_ingress_module):
        """Test that None is returned when attribute doesn't exist."""
        record = {"messageAttributes": {}}
        result = webhook_ingress_module.get_message_attribute(record, "x-github-event")
        assert result is None

    def test_returns_none_when_message_attributes_missing(self, webhook_ingress_module):
        """Test that None is returned when messageAttributes key is missing."""
        record = {}
        result = webhook_ingress_module.get_message_attribute(record, "x-github-event")
        assert result is None

    def test_returns_none_when_string_value_missing(self, webhook_ingress_module):
        """Test that None is returned when stringValue is missing from attribute."""
        record = {"messageAttributes": {"x-github-event": {"dataType": "String"}}}
        result = webhook_ingress_module.get_message_attribute(record, "x-github-event")
        assert result is None


class TestIsWebhookIngressQueue:
    """Tests for is_webhook_ingress_queue function."""

    def test_returns_true_for_ingress_queue(self, webhook_ingress_module):
        """Test that True is returned for ingress queue ARN."""
        arn = "arn:aws:sqs:us-east-1:123456789012:MyIngressQueue"
        assert webhook_ingress_module.is_webhook_ingress_queue(arn) is True

    def test_returns_false_for_non_ingress_queue(self, webhook_ingress_module):
        """Test that False is returned for non-ingress queue ARN."""
        arn = "arn:aws:sqs:us-east-1:123456789012:MyOtherQueue"
        assert webhook_ingress_module.is_webhook_ingress_queue(arn) is False

    def test_returns_true_for_webhook_ingress(self, webhook_ingress_module):
        """Test that True is returned for webhook_ingress queue ARN."""
        arn = "arn:aws:sqs:us-east-1:123456789012:webhook_Ingress_queue"
        assert webhook_ingress_module.is_webhook_ingress_queue(arn) is True


class TestIngressHandler:
    """Tests for IngressHandler class."""

    def test_init_stores_deps(self, webhook_ingress_module, mock_ingress_deps):
        """Test that init stores dependencies."""
        handler = webhook_ingress_module.IngressHandler(mock_ingress_deps)
        assert handler.get_deps() == mock_ingress_deps


class TestIngressHandlerHandle:
    """Tests for IngressHandler.handle method."""

    @pytest.fixture
    def handler(self, webhook_ingress_module, mock_ingress_deps):
        """Create an IngressHandler with mock dependencies."""
        return webhook_ingress_module.IngressHandler(mock_ingress_deps)

    def test_handle_workflow_job_queued(self, handler, mock_ingress_deps):
        """Test handling a workflow_job with action=queued."""
        body = {
            "action": "queued",
            "workflow_job": {"id": 123, "run_id": 456, "labels": ["self-hosted", "linux", "ec2"]},
            "repository": {"full_name": "org/repo"}
        }
        record = _create_sqs_record(body)
        result = _run_async(handler.handle(record))
        mock_ingress_deps.enqueue_job.assert_called_once()
        assert result["success"] is True and result["routed"] == "/v1/runners"

    def test_handle_workflow_job_cancelled(self, handler, mock_ingress_deps):
        """Test handling a workflow_job with action=cancelled is ignored.

        Runners are ephemeral and self-terminate, so no termination action needed.
        """
        body = {
            "action": "cancelled",
            "workflow_job": {"id": 123, "run_id": 456, "runner_name": "runner-1"},
            "repository": {"full_name": "org/repo"}
        }
        record = _create_sqs_record(body)
        result = _run_async(handler.handle(record))
        mock_ingress_deps.enqueue_ignored.assert_called_once()
        assert result["success"] is True and result["routed"] == "ignored_events"

    def test_handle_workflow_job_completed(self, handler, mock_ingress_deps):
        """Test handling a workflow_job with action=completed is ignored.

        Runners are ephemeral and self-terminate, so no termination action needed.
        """
        body = {
            "action": "completed",
            "workflow_job": {"id": 123, "run_id": 456, "runner_name": "runner-1"},
            "repository": {"full_name": "org/repo"}
        }
        record = _create_sqs_record(body)
        result = _run_async(handler.handle(record))
        assert result["success"] is True and result["routed"] == "ignored_events"

    def test_handle_workflow_job_in_progress_ignored(self, handler, mock_ingress_deps):
        """Test handling a workflow_job with action=in_progress is ignored."""
        body = {"action": "in_progress", "workflow_job": {"id": 123, "run_id": 456}, "repository": {"full_name": "org/repo"}}
        record = _create_sqs_record(body)
        result = _run_async(handler.handle(record))
        mock_ingress_deps.enqueue_ignored.assert_called_once()
        assert result["success"] is True and result["routed"] == "ignored_events"

    def test_handle_workflow_job_no_runner_type(self, handler, mock_ingress_deps):
        """Test handling a workflow_job with no matching runner type."""
        mock_ingress_deps.get_runner_type.return_value = (None, None)
        body = {
            "action": "queued",
            "workflow_job": {"id": 123, "run_id": 456, "labels": ["ubuntu-latest"]},
            "repository": {"full_name": "org/repo"}
        }
        record = _create_sqs_record(body)
        result = _run_async(handler.handle(record))
        assert result["success"] is True and result["routed"] == "ignored_events"

    def test_handle_workflow_run(self, handler, mock_ingress_deps):
        """Test handling a workflow_run event."""
        body = {"action": "completed", "workflow_run": {"id": 789, "conclusion": "success"}}
        record = _create_sqs_record(body, event_type="workflow_run")
        result = _run_async(handler.handle(record))
        assert result["success"] is True and result["routed"] == "acknowledged"

    def test_handle_ping_event(self, handler, mock_ingress_deps):
        """Test handling a ping event."""
        body = {"zen": "Half measures are as bad as nothing at all."}
        record = _create_sqs_record(body, event_type="ping")
        result = _run_async(handler.handle(record))
        assert result["success"] is True and result["routed"] == "ping_acknowledged"

    def test_handle_unknown_event_type(self, handler, mock_ingress_deps):
        """Test handling an unknown event type."""
        body = {"action": "created"}
        record = _create_sqs_record(body, event_type="issues")
        result = _run_async(handler.handle(record))
        mock_ingress_deps.enqueue_ignored.assert_called_once()
        assert result["success"] is True and result["routed"] == "ignored_events"

    def test_handle_duplicate_delivery(self, handler, mock_ingress_deps):
        """Test handling a duplicate delivery is skipped."""
        mock_ingress_deps.check_idempotency.return_value = True
        record = _create_sqs_record({"action": "queued"})
        result = _run_async(handler.handle(record))
        expected = (True, True, "duplicate")
        assert (result["success"], result["skipped"], result["reason"]) == expected

    def test_handle_invalid_signature(self, handler, mock_ingress_deps):
        """Test handling an invalid signature."""
        mock_ingress_deps.verify_signature.return_value = False
        record = _create_sqs_record({"action": "queued"}, signature="sha256=invalid")
        result = _run_async(handler.handle(record))
        mock_ingress_deps.publish_metric.assert_called_with("InvalidSignature", 1.0, "Count")
        expected = (True, True, "invalid_signature")
        assert (result["success"], result["skipped"], result["reason"]) == expected

    def test_handle_no_signature_proceeds(self, handler, mock_ingress_deps):
        """Test handling without signature proceeds."""
        body = {
            "action": "queued",
            "workflow_job": {"id": 123, "run_id": 456, "labels": ["self-hosted"]},
            "repository": {"full_name": "org/repo"}
        }
        record = _create_sqs_record(body, signature=None)
        result = _run_async(handler.handle(record))
        mock_ingress_deps.verify_signature.assert_not_called()
        assert result["success"] is True

    def test_handle_invalid_json_body(self, handler, mock_ingress_deps):
        """Test handling an invalid JSON body is skipped."""
        record = {"body": "not-valid-json", "messageAttributes": _create_message_attrs()}
        result = _run_async(handler.handle(record))
        expected = (True, True, "invalid_json")
        assert (result["success"], result["skipped"], result["reason"]) == expected

    def test_handle_signature_verification_error(self, handler, mock_ingress_deps):
        """Test handling a signature verification error."""
        mock_ingress_deps.get_webhook_secret.side_effect = RuntimeError("Secret unavailable")
        record = _create_sqs_record({"action": "queued"})
        result = _run_async(handler.handle(record))
        assert result["success"] is False and "Secret unavailable" in result["error"]

    def test_handle_no_delivery_id_skips_idempotency(self, handler, mock_ingress_deps):
        """Test handling without delivery ID skips idempotency check."""
        body = {
            "action": "queued",
            "workflow_job": {"id": 123, "run_id": 456, "labels": ["self-hosted"]},
            "repository": {"full_name": "org/repo"}
        }
        record = _create_sqs_record(body, delivery_id=None)
        result = _run_async(handler.handle(record))
        mock_ingress_deps.check_idempotency.assert_not_called()
        assert result["success"] is True

    def test_handle_publishes_processing_time_metric(self, handler, mock_ingress_deps):
        """Test that processing time metric is published."""
        body = {"action": "completed", "workflow_run": {"id": 789, "conclusion": "success"}}
        record = _create_sqs_record(body, event_type="workflow_run")
        _run_async(handler.handle(record))
        mock_ingress_deps.publish_metric.assert_called()
        call_args = mock_ingress_deps.publish_metric.call_args_list[-1]
        expected = ("WebhookIngressProcessingTime", "Milliseconds")
        assert (call_args[0][0], call_args[0][2]) == expected

    def test_handle_enqueue_job_failure(self, handler, mock_ingress_deps):
        """Test handling when enqueue_job fails."""
        mock_ingress_deps.enqueue_job.return_value = {"success": False}
        body = {
            "action": "queued",
            "workflow_job": {"id": 123, "run_id": 456, "labels": ["self-hosted"]},
            "repository": {"full_name": "org/repo"}
        }
        record = _create_sqs_record(body)
        result = _run_async(handler.handle(record))
        assert result["success"] is False

    # Note: test_handle_enqueue_cancellation_failure removed - runners are ephemeral

    def test_handle_empty_body(self, handler, mock_ingress_deps):
        """Test handling an empty body."""
        record = {"body": "", "messageAttributes": _create_message_attrs()}
        result = _run_async(handler.handle(record))
        expected = (True, True, "invalid_json")
        assert (result["success"], result["skipped"], result["reason"]) == expected

    def test_handle_signature_value_error(self, handler, mock_ingress_deps):
        """Test handling a ValueError during signature verification."""
        mock_ingress_deps.verify_signature.side_effect = ValueError("Invalid value")
        record = _create_sqs_record({"action": "queued"})
        result = _run_async(handler.handle(record))
        assert result["success"] is False and "Invalid value" in result["error"]

    def test_handle_signature_type_error(self, handler, mock_ingress_deps):
        """Test handling a TypeError during signature verification."""
        mock_ingress_deps.verify_signature.side_effect = TypeError("Type error")
        record = _create_sqs_record({"action": "queued"})
        result = _run_async(handler.handle(record))
        assert result["success"] is False and "Type error" in result["error"]


class TestIngressHandlerExtractHeadersAndBody:
    """Tests for IngressHandler._extract_headers_and_body method."""

    @pytest.fixture
    def mock_ingress_deps(self):
        """Create mock dependencies."""
        return MagicMock()

    @pytest.fixture
    def handler(self, webhook_ingress_module, mock_ingress_deps):
        """Create an IngressHandler with mock dependencies."""
        return webhook_ingress_module.IngressHandler(mock_ingress_deps)

    def test_extracts_all_headers(self, handler):
        """Test that all headers are extracted."""
        record = _create_sqs_record({"test": "data"})
        headers, body_str, payload = handler._extract_headers_and_body(record)
        expected = ("workflow_job", "sha256=abc", "delivery-123", {"test": "data"})
        actual = (
            headers["x-github-event"],
            headers["x-hub-signature-256"],
            headers["x-github-delivery"],
            payload
        )
        assert actual == expected

    def test_handles_missing_headers(self, handler):
        """Test handling when some headers are missing."""
        record = _create_sqs_record({"test": "data"}, event_type="ping", signature=None, delivery_id=None)
        headers, body_str, payload = handler._extract_headers_and_body(record)
        headers_match = headers == {"x-github-event": "ping"}
        sig_missing = "x-hub-signature-256" not in headers
        delivery_missing = "x-github-delivery" not in headers
        assert headers_match and sig_missing and delivery_missing

    def test_handles_invalid_json(self, handler):
        """Test handling invalid JSON body."""
        record = {
            "body": "not-json",
            "messageAttributes": {}
        }
        headers, body_str, payload = handler._extract_headers_and_body(record)
        assert payload is None and body_str == "not-json"

    def test_handles_empty_body(self, handler):
        """Test handling empty body."""
        record = {"body": "", "messageAttributes": {}}
        headers, body_str, payload = handler._extract_headers_and_body(record)
        assert payload is None and body_str == ""

    def test_handles_missing_body(self, handler):
        """Test handling missing body key."""
        record = {"messageAttributes": {}}
        headers, body_str, payload = handler._extract_headers_and_body(record)
        assert body_str == "" and payload is None
