"""Unit tests for webhook_ingress module."""

import json
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from .conftest import load_lambda_module, run_async


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

    def test_get_deps_returns_same_object(self, webhook_ingress_module, mock_ingress_deps):
        """Test that get_deps returns the same deps object."""
        handler = webhook_ingress_module.IngressHandler(mock_ingress_deps)
        assert handler.get_deps() is mock_ingress_deps


class TestIngressHandlerHandle:
    """Tests for IngressHandler.handle method."""

    @pytest.fixture
    def handler(self, webhook_ingress_module, mock_ingress_deps):
        """Create an IngressHandler with mock dependencies."""
        return webhook_ingress_module.IngressHandler(mock_ingress_deps)

    @pytest.mark.parametrize(
        "action", ["queued", "cancelled", "completed", "in_progress"]
    )
    def test_handle_workflow_job_is_archived(self, handler, action):
        """Test every workflow_job action is archived now nothing serves one."""
        body = {
            "action": action,
            "workflow_job": {"id": 123, "run_id": 456},
            "repository": {"full_name": "org/repo"}
        }
        result = run_async(handler.handle(_create_sqs_record(body)))
        assert result["routed"] == "ignored_events"

    def test_handle_workflow_job_reaches_the_archive(self, handler, mock_ingress_deps):
        """Test a workflow_job is handed to the ignored-event archive."""
        run_async(handler.handle(_create_sqs_record({
            "action": "queued",
            "workflow_job": {"id": 1},
            "repository": {"full_name": "org/repo"}
        })))
        assert mock_ingress_deps.enqueue_ignored.call_count == 1

    def test_handle_workflow_run(self, handler):
        """Test handling a workflow_run event."""
        body = {"action": "completed", "workflow_run": {"id": 789, "conclusion": "success"}}
        record = _create_sqs_record(body, event_type="workflow_run")
        result = run_async(handler.handle(record))
        assert result["success"] is True and result["routed"] == "acknowledged"

    def test_handle_ping_event(self, handler):
        """Test handling a ping event."""
        body = {"zen": "Half measures are as bad as nothing at all."}
        record = _create_sqs_record(body, event_type="ping")
        result = run_async(handler.handle(record))
        assert result["success"] is True and result["routed"] == "ping_acknowledged"

    def test_handle_unknown_event_type(self, handler, mock_ingress_deps):
        """Test handling an unknown event type."""
        body = {"action": "created"}
        record = _create_sqs_record(body, event_type="issues")
        result = run_async(handler.handle(record))
        mock_ingress_deps.enqueue_ignored.assert_called_once()
        assert result["success"] is True and result["routed"] == "ignored_events"

    def test_handle_duplicate_delivery(self, handler, mock_ingress_deps):
        """Test handling a duplicate delivery is skipped."""
        mock_ingress_deps.check_idempotency.return_value = True
        record = _create_sqs_record({"action": "queued"})
        result = run_async(handler.handle(record))
        expected = (True, True, "duplicate")
        assert (result["success"], result["skipped"], result["reason"]) == expected

    def test_handle_invalid_signature(self, handler, mock_ingress_deps):
        """Test handling an invalid signature."""
        mock_ingress_deps.verify_signature.return_value = False
        record = _create_sqs_record({"action": "queued"}, signature="sha256=invalid")
        result = run_async(handler.handle(record))
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
        result = run_async(handler.handle(record))
        mock_ingress_deps.verify_signature.assert_not_called()
        assert result["success"] is True

    def test_handle_invalid_json_body(self, handler):
        """Test handling an invalid JSON body is skipped."""
        record = {"body": "not-valid-json", "messageAttributes": _create_message_attrs()}
        result = run_async(handler.handle(record))
        expected = (True, True, "invalid_json")
        assert (result["success"], result["skipped"], result["reason"]) == expected

    def test_handle_signature_verification_error(self, handler, mock_ingress_deps):
        """Test handling a signature verification error."""
        mock_ingress_deps.get_webhook_secret.side_effect = RuntimeError("Secret unavailable")
        record = _create_sqs_record({"action": "queued"})
        result = run_async(handler.handle(record))
        assert result["success"] is False and "Secret unavailable" in result["error"]

    def test_handle_no_delivery_id_skips_idempotency(self, handler, mock_ingress_deps):
        """Test handling without delivery ID skips idempotency check."""
        body = {
            "action": "queued",
            "workflow_job": {"id": 123, "run_id": 456, "labels": ["self-hosted"]},
            "repository": {"full_name": "org/repo"}
        }
        record = _create_sqs_record(body, delivery_id=None)
        result = run_async(handler.handle(record))
        mock_ingress_deps.check_idempotency.assert_not_called()
        assert result["success"] is True

    def test_handle_publishes_processing_time_metric(self, handler, mock_ingress_deps):
        """Test that processing time metric is published."""
        body = {"action": "completed", "workflow_run": {"id": 789, "conclusion": "success"}}
        record = _create_sqs_record(body, event_type="workflow_run")
        run_async(handler.handle(record))
        mock_ingress_deps.publish_metric.assert_called()
        call_args = mock_ingress_deps.publish_metric.call_args_list[-1]
        expected = ("WebhookIngressProcessingTime", "Milliseconds")
        assert (call_args[0][0], call_args[0][2]) == expected

    def test_handle_empty_body(self, handler):
        """Test handling an empty body."""
        record = {"body": "", "messageAttributes": _create_message_attrs()}
        result = run_async(handler.handle(record))
        expected = (True, True, "invalid_json")
        assert (result["success"], result["skipped"], result["reason"]) == expected

    def test_handle_signature_value_error(self, handler, mock_ingress_deps):
        """Test handling a ValueError during signature verification."""
        mock_ingress_deps.verify_signature.side_effect = ValueError("Invalid value")
        record = _create_sqs_record({"action": "queued"})
        result = run_async(handler.handle(record))
        assert result["success"] is False and "Invalid value" in result["error"]

    def test_handle_signature_type_error(self, handler, mock_ingress_deps):
        """Test handling a TypeError during signature verification."""
        mock_ingress_deps.verify_signature.side_effect = TypeError("Type error")
        record = _create_sqs_record({"action": "queued"})
        result = run_async(handler.handle(record))
        assert result["success"] is False and "Type error" in result["error"]


class TestIngressHandlerExtractHeadersAndBody:
    """Tests for IngressHandler.extract_headers_and_body method."""

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
        headers, _body_str, payload = handler.extract_headers_and_body(record)
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
        record = _create_sqs_record(
            {"test": "data"}, event_type="ping", signature=None, delivery_id=None
        )
        headers, _body_str, _payload = handler.extract_headers_and_body(record)
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
        _headers, body_str, payload = handler.extract_headers_and_body(record)
        assert payload is None and body_str == "not-json"

    def test_handles_empty_body(self, handler):
        """Test handling empty body."""
        record = {"body": "", "messageAttributes": {}}
        _headers, body_str, payload = handler.extract_headers_and_body(record)
        assert payload is None and body_str == ""

    def test_handles_missing_body(self, handler):
        """Test handling missing body key."""
        record = {"messageAttributes": {}}
        _headers, body_str, payload = handler.extract_headers_and_body(record)
        assert body_str == "" and payload is None
