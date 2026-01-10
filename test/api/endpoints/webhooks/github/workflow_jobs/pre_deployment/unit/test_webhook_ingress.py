"""Unit tests for webhook_ingress module."""

import asyncio
import json
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


@pytest.fixture(name="webhook_ingress_module")
def webhook_ingress_module_fixture():
    """Load webhook_ingress module for testing."""
    module = load_lambda_module("common/webhook_ingress.py", "webhook_ingress")
    yield module


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

    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies for IngressHandler."""
        deps = MagicMock()
        deps.get_webhook_secret = AsyncMock(return_value="test-secret")
        deps.verify_signature = MagicMock(return_value=True)
        deps.publish_metric = MagicMock()
        deps.check_idempotency = AsyncMock(return_value=False)
        deps.get_runner_type = MagicMock(return_value=("ec2", "m5.large"))
        deps.enqueue_job = AsyncMock(return_value={"success": True})
        deps.enqueue_cancellation = AsyncMock(return_value={"success": True})
        deps.enqueue_ignored = MagicMock()
        return deps

    @pytest.fixture
    def handler(self, webhook_ingress_module, mock_deps):
        """Create an IngressHandler with mock dependencies."""
        return webhook_ingress_module.IngressHandler(mock_deps)

    def test_init_stores_deps(self, webhook_ingress_module, mock_deps):
        """Test that init stores dependencies."""
        handler = webhook_ingress_module.IngressHandler(mock_deps)
        assert handler.get_deps() == mock_deps


class TestIngressHandlerHandle:
    """Tests for IngressHandler.handle method."""

    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies for IngressHandler."""
        deps = MagicMock()
        deps.get_webhook_secret = AsyncMock(return_value="test-secret")
        deps.verify_signature = MagicMock(return_value=True)
        deps.publish_metric = MagicMock()
        deps.check_idempotency = AsyncMock(return_value=False)
        deps.get_runner_type = MagicMock(return_value=("ec2", "m5.large"))
        deps.enqueue_job = AsyncMock(return_value={"success": True})
        deps.enqueue_cancellation = AsyncMock(return_value={"success": True})
        deps.enqueue_ignored = MagicMock()
        return deps

    @pytest.fixture
    def handler(self, webhook_ingress_module, mock_deps):
        """Create an IngressHandler with mock dependencies."""
        return webhook_ingress_module.IngressHandler(mock_deps)

    def test_handle_workflow_job_queued(self, handler, mock_deps):
        """Test handling a workflow_job with action=queued."""
        record = {
            "body": json.dumps({
                "action": "queued",
                "workflow_job": {
                    "id": 123,
                    "run_id": 456,
                    "labels": ["self-hosted", "linux", "ec2"]
                },
                "repository": {"full_name": "org/repo"}
            }),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is True
        assert result["routed"] == "/v1/runners"
        mock_deps.enqueue_job.assert_called_once()

    def test_handle_workflow_job_cancelled(self, handler, mock_deps):
        """Test handling a workflow_job with action=cancelled."""
        record = {
            "body": json.dumps({
                "action": "cancelled",
                "workflow_job": {
                    "id": 123,
                    "run_id": 456,
                    "runner_name": "runner-1"
                },
                "repository": {"full_name": "org/repo"}
            }),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is True
        assert result["routed"] == "cancellation_queue"
        mock_deps.enqueue_cancellation.assert_called_once()

    def test_handle_workflow_job_completed(self, handler, mock_deps):
        """Test handling a workflow_job with action=completed."""
        record = {
            "body": json.dumps({
                "action": "completed",
                "workflow_job": {
                    "id": 123,
                    "run_id": 456,
                    "runner_name": "runner-1"
                },
                "repository": {"full_name": "org/repo"}
            }),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is True
        assert result["routed"] == "cancellation_queue"

    def test_handle_workflow_job_in_progress_ignored(self, handler, mock_deps):
        """Test handling a workflow_job with action=in_progress is ignored."""
        record = {
            "body": json.dumps({
                "action": "in_progress",
                "workflow_job": {"id": 123, "run_id": 456},
                "repository": {"full_name": "org/repo"}
            }),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is True
        assert result["routed"] == "ignored_events"
        mock_deps.enqueue_ignored.assert_called_once()

    def test_handle_workflow_job_no_runner_type(self, handler, mock_deps):
        """Test handling a workflow_job with no matching runner type."""
        mock_deps.get_runner_type.return_value = (None, None)
        record = {
            "body": json.dumps({
                "action": "queued",
                "workflow_job": {
                    "id": 123,
                    "run_id": 456,
                    "labels": ["ubuntu-latest"]
                },
                "repository": {"full_name": "org/repo"}
            }),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is True
        assert result["routed"] == "ignored_events"

    def test_handle_workflow_run(self, handler, mock_deps):
        """Test handling a workflow_run event."""
        record = {
            "body": json.dumps({
                "action": "completed",
                "workflow_run": {
                    "id": 789,
                    "conclusion": "success"
                }
            }),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_run"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is True
        assert result["routed"] == "acknowledged"

    def test_handle_ping_event(self, handler, mock_deps):
        """Test handling a ping event."""
        record = {
            "body": json.dumps({"zen": "Half measures are as bad as nothing at all."}),
            "messageAttributes": {
                "x-github-event": {"stringValue": "ping"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is True
        assert result["routed"] == "ping_acknowledged"

    def test_handle_unknown_event_type(self, handler, mock_deps):
        """Test handling an unknown event type."""
        record = {
            "body": json.dumps({"action": "created"}),
            "messageAttributes": {
                "x-github-event": {"stringValue": "issues"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is True
        assert result["routed"] == "ignored_events"
        mock_deps.enqueue_ignored.assert_called_once()

    def test_handle_duplicate_delivery(self, handler, mock_deps):
        """Test handling a duplicate delivery is skipped."""
        mock_deps.check_idempotency.return_value = True
        record = {
            "body": json.dumps({"action": "queued"}),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is True
        assert result["skipped"] is True
        assert result["reason"] == "duplicate"

    def test_handle_invalid_signature(self, handler, mock_deps):
        """Test handling an invalid signature."""
        mock_deps.verify_signature.return_value = False
        record = {
            "body": json.dumps({"action": "queued"}),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-hub-signature-256": {"stringValue": "sha256=invalid"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is True
        assert result["skipped"] is True
        assert result["reason"] == "invalid_signature"
        mock_deps.publish_metric.assert_called_with("InvalidSignature", 1.0, "Count")

    def test_handle_no_signature_proceeds(self, handler, mock_deps):
        """Test handling without signature proceeds."""
        record = {
            "body": json.dumps({
                "action": "queued",
                "workflow_job": {
                    "id": 123,
                    "run_id": 456,
                    "labels": ["self-hosted"]
                },
                "repository": {"full_name": "org/repo"}
            }),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is True
        mock_deps.verify_signature.assert_not_called()

    def test_handle_invalid_json_body(self, handler, mock_deps):
        """Test handling an invalid JSON body is skipped."""
        record = {
            "body": "not-valid-json",
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is True
        assert result["skipped"] is True
        assert result["reason"] == "invalid_json"

    def test_handle_signature_verification_error(self, handler, mock_deps):
        """Test handling a signature verification error."""
        mock_deps.get_webhook_secret.side_effect = RuntimeError("Secret unavailable")
        record = {
            "body": json.dumps({"action": "queued"}),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is False
        assert "Secret unavailable" in result["error"]

    def test_handle_no_delivery_id_skips_idempotency(self, handler, mock_deps):
        """Test handling without delivery ID skips idempotency check."""
        record = {
            "body": json.dumps({
                "action": "queued",
                "workflow_job": {
                    "id": 123,
                    "run_id": 456,
                    "labels": ["self-hosted"]
                },
                "repository": {"full_name": "org/repo"}
            }),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is True
        mock_deps.check_idempotency.assert_not_called()

    def test_handle_publishes_processing_time_metric(self, handler, mock_deps):
        """Test that processing time metric is published."""
        record = {
            "body": json.dumps({
                "action": "completed",
                "workflow_run": {"id": 789, "conclusion": "success"}
            }),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_run"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        _run_async(handler.handle(record))
        mock_deps.publish_metric.assert_called()
        call_args = mock_deps.publish_metric.call_args_list[-1]
        assert call_args[0][0] == "WebhookIngressProcessingTime"
        assert call_args[0][2] == "Milliseconds"

    def test_handle_enqueue_job_failure(self, handler, mock_deps):
        """Test handling when enqueue_job fails."""
        mock_deps.enqueue_job.return_value = {"success": False}
        record = {
            "body": json.dumps({
                "action": "queued",
                "workflow_job": {
                    "id": 123,
                    "run_id": 456,
                    "labels": ["self-hosted"]
                },
                "repository": {"full_name": "org/repo"}
            }),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is False

    def test_handle_enqueue_cancellation_failure(self, handler, mock_deps):
        """Test handling when enqueue_cancellation fails."""
        mock_deps.enqueue_cancellation.return_value = {"success": False}
        record = {
            "body": json.dumps({
                "action": "cancelled",
                "workflow_job": {
                    "id": 123,
                    "run_id": 456,
                    "runner_name": "runner-1"
                },
                "repository": {"full_name": "org/repo"}
            }),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is False

    def test_handle_empty_body(self, handler, mock_deps):
        """Test handling an empty body."""
        record = {
            "body": "",
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is True
        assert result["skipped"] is True
        assert result["reason"] == "invalid_json"

    def test_handle_signature_value_error(self, handler, mock_deps):
        """Test handling a ValueError during signature verification."""
        mock_deps.verify_signature.side_effect = ValueError("Invalid value")
        record = {
            "body": json.dumps({"action": "queued"}),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is False
        assert "Invalid value" in result["error"]

    def test_handle_signature_type_error(self, handler, mock_deps):
        """Test handling a TypeError during signature verification."""
        mock_deps.verify_signature.side_effect = TypeError("Type error")
        record = {
            "body": json.dumps({"action": "queued"}),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        result = _run_async(handler.handle(record))
        assert result["success"] is False
        assert "Type error" in result["error"]


class TestIngressHandlerExtractHeadersAndBody:
    """Tests for IngressHandler._extract_headers_and_body method."""

    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies."""
        return MagicMock()

    @pytest.fixture
    def handler(self, webhook_ingress_module, mock_deps):
        """Create an IngressHandler with mock dependencies."""
        return webhook_ingress_module.IngressHandler(mock_deps)

    def test_extracts_all_headers(self, handler):
        """Test that all headers are extracted."""
        record = {
            "body": json.dumps({"test": "data"}),
            "messageAttributes": {
                "x-github-event": {"stringValue": "workflow_job"},
                "x-hub-signature-256": {"stringValue": "sha256=abc"},
                "x-github-delivery": {"stringValue": "delivery-123"}
            }
        }
        headers, body_str, payload = handler._extract_headers_and_body(record)
        assert headers["x-github-event"] == "workflow_job"
        assert headers["x-hub-signature-256"] == "sha256=abc"
        assert headers["x-github-delivery"] == "delivery-123"
        assert payload == {"test": "data"}

    def test_handles_missing_headers(self, handler):
        """Test handling when some headers are missing."""
        record = {
            "body": json.dumps({"test": "data"}),
            "messageAttributes": {
                "x-github-event": {"stringValue": "ping"}
            }
        }
        headers, body_str, payload = handler._extract_headers_and_body(record)
        assert headers == {"x-github-event": "ping"}
        assert "x-hub-signature-256" not in headers
        assert "x-github-delivery" not in headers

    def test_handles_invalid_json(self, handler):
        """Test handling invalid JSON body."""
        record = {
            "body": "not-json",
            "messageAttributes": {}
        }
        headers, body_str, payload = handler._extract_headers_and_body(record)
        assert payload is None
        assert body_str == "not-json"

    def test_handles_empty_body(self, handler):
        """Test handling empty body."""
        record = {"body": "", "messageAttributes": {}}
        headers, body_str, payload = handler._extract_headers_and_body(record)
        assert payload is None
        assert body_str == ""

    def test_handles_missing_body(self, handler):
        """Test handling missing body key."""
        record = {"messageAttributes": {}}
        headers, body_str, payload = handler._extract_headers_and_body(record)
        assert body_str == ""
        assert payload is None
