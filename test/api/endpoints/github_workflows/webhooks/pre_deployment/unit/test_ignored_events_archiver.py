"""Unit tests for ignored_events_archiver Lambda."""
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, List, Optional
from unittest.mock import MagicMock, patch

import pytest

from .conftest import load_lambda_module


def _create_capturing_s3_mock() -> tuple:
    """Create an S3 mock that captures put_object body.

    Returns:
        tuple: (mock_s3, captured list where captured[0] will be the body)
    """
    mock_s3 = MagicMock()
    captured: List[Optional[str]] = [None]

    def capture_put_object(**kwargs):
        captured[0] = kwargs.get('Body')
        return {}

    mock_s3.put_object.side_effect = capture_put_object
    return mock_s3, captured


@contextmanager
def _mock_archiver_success_context(archiver_module, records: list) -> Iterator[MagicMock]:
    """Context manager for successful archiver test setup.

    Args:
        archiver_module: The archiver module.
        records: List of SQS records to process.

    Yields:
        mock_s3: The mock S3 client.
    """
    mock_s3 = MagicMock()
    mock_s3.put_object.return_value = {}
    with patch.object(archiver_module, 'get_sqs_records', return_value=records):
        with patch.object(archiver_module, 'get_s3_client', return_value=mock_s3):
            yield mock_s3


@pytest.fixture(name="archiver_module")
def archiver_module_fixture():
    """Load ignored_events_archiver module for testing."""
    env_vars = {
        'ARCHIVE_BUCKET_NAME': 'test-archive-bucket',
    }
    with patch.dict('os.environ', env_vars):
        with patch('common.aws_clients.get_s3_client'):
            module = load_lambda_module(
                "ignored_events_archiver.py", "ignored_events_archiver"
            )
            yield module


class TestBuildS3Key:
    """Tests for _build_s3_key function."""

    def test_builds_key_with_valid_timestamp(self, archiver_module):
        """Test that S3 key is built correctly with valid timestamp."""
        timestamp = "2024-03-15T14:30:00+00:00"
        message_id = "msg-123"
        result = archiver_module._build_s3_key(timestamp, message_id)
        assert result == "ignored-events/2024/03/15/14/msg-123.json"

    def test_builds_key_with_z_suffix_timestamp(self, archiver_module):
        """Test that Z suffix timestamp is parsed correctly."""
        timestamp = "2024-06-20T09:15:00Z"
        message_id = "msg-456"
        result = archiver_module._build_s3_key(timestamp, message_id)
        assert result == "ignored-events/2024/06/20/09/msg-456.json"

    def test_uses_current_time_for_invalid_timestamp(self, archiver_module):
        """Test that current time is used for invalid timestamp."""
        timestamp = "not-a-valid-timestamp"
        message_id = "msg-789"
        result = archiver_module._build_s3_key(timestamp, message_id)
        # Should still build a valid path using current time
        assert result.startswith("ignored-events/") and result.endswith("/msg-789.json")

    def test_pads_month_and_day_with_zeros(self, archiver_module):
        """Test that single-digit month and day are zero-padded."""
        timestamp = "2024-01-05T03:07:00+00:00"
        message_id = "msg-abc"
        result = archiver_module._build_s3_key(timestamp, message_id)
        assert result == "ignored-events/2024/01/05/03/msg-abc.json"


class TestArchiveEvent:
    """Tests for _archive_event function."""

    def test_returns_error_when_bucket_not_configured(self, archiver_module):
        """Test that error is returned when bucket is not configured."""
        with patch.dict('os.environ', {'ARCHIVE_BUCKET_NAME': ''}):
            record = {"body": '{"event_data": {}}', "messageId": "msg-123"}
            result = archiver_module._archive_event(record)
            assert result["success"] is False and "not configured" in result["error"]

    def test_archives_event_successfully(self, archiver_module):
        """Test that event is archived successfully."""
        mock_s3 = MagicMock()
        mock_s3.put_object.return_value = {}
        record = {
            "body": json.dumps({
                "event_data": {"action": "test"},
                "reason": "test reason",
                "timestamp": "2024-03-15T14:30:00+00:00"
            }),
            "messageId": "msg-123",
            "attributes": {"ApproximateReceiveCount": "1"}
        }
        with patch.object(archiver_module, 'get_s3_client', return_value=mock_s3):
            result = archiver_module._archive_event(record)
            assert result["success"] is True and "ignored-events/" in result["key"]

    def test_includes_archived_at_timestamp(self, archiver_module):
        """Test that archived_at timestamp is included in archived event."""
        mock_s3, captured = _create_capturing_s3_mock()
        record = {
            "body": json.dumps({"event_data": {}, "timestamp": "2024-01-01T00:00:00Z"}),
            "messageId": "msg-456"
        }
        with patch.object(archiver_module, 'get_s3_client', return_value=mock_s3):
            archiver_module._archive_event(record)
            archived_event = json.loads(captured[0])
            assert "archived_at" in archived_event

    def test_returns_error_on_json_decode_error(self, archiver_module):
        """Test that error is returned on JSON decode error."""
        record = {"body": "not valid json", "messageId": "msg-789"}
        result = archiver_module._archive_event(record)
        assert result["success"] is False

    def test_returns_error_on_s3_client_error(self, archiver_module):
        """Test that error is returned on S3 client error."""
        from botocore.exceptions import ClientError
        mock_s3 = MagicMock()
        mock_s3.put_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}},
            "PutObject"
        )
        record = {
            "body": json.dumps({"event_data": {}, "timestamp": "2024-01-01T00:00:00Z"}),
            "messageId": "msg-error"
        }
        with patch.object(archiver_module, 'get_s3_client', return_value=mock_s3):
            result = archiver_module._archive_event(record)
            assert result["success"] is False

    def test_uses_current_time_when_no_timestamp(self, archiver_module):
        """Test that current time is used when no timestamp in body."""
        mock_s3 = MagicMock()
        mock_s3.put_object.return_value = {}
        record = {
            "body": json.dumps({"event_data": {}}),
            "messageId": "msg-no-ts"
        }
        with patch.object(archiver_module, 'get_s3_client', return_value=mock_s3):
            result = archiver_module._archive_event(record)
            assert result["success"] is True

    def test_includes_sqs_attributes_in_archive(self, archiver_module):
        """Test that SQS attributes are included in archived event."""
        mock_s3, captured = _create_capturing_s3_mock()
        record = {
            "body": json.dumps({"event_data": {}, "timestamp": "2024-01-01T00:00:00Z"}),
            "messageId": "msg-attrs",
            "attributes": {"ApproximateReceiveCount": "3"}
        }
        with patch.object(archiver_module, 'get_s3_client', return_value=mock_s3):
            archiver_module._archive_event(record)
            archived_event = json.loads(captured[0])
            assert archived_event["sqs_attributes"]["ApproximateReceiveCount"] == "3"


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    def test_returns_empty_response_when_no_records(self, archiver_module, lambda_context):
        """Test that empty response is returned when no records."""
        event = {"Records": []}
        empty_resp_patch = patch.object(
            archiver_module, 'empty_records_response', return_value={"statusCode": 200}
        )
        with patch.object(archiver_module, 'get_sqs_records', return_value=None):
            with empty_resp_patch:
                result = archiver_module.lambda_handler(event, lambda_context)
                assert result["statusCode"] == 200

    def test_archives_events_successfully(self, archiver_module, lambda_context):
        """Test that events are archived successfully."""
        record = {
            "body": json.dumps({"event_data": {}, "timestamp": "2024-01-01T00:00:00Z"}),
            "messageId": "msg-success"
        }
        with _mock_archiver_success_context(archiver_module, [record]):
            with patch.object(archiver_module, 'publish_metric'):
                with patch.object(archiver_module, 'count_results', return_value=(1, 0)):
                    result = archiver_module.lambda_handler(event={}, _context=lambda_context)
                    body = json.loads(result["body"])
                    assert result["statusCode"] == 200 and body["success"] == 1

    def test_publishes_events_archived_metric(self, archiver_module, lambda_context):
        """Test that EventsArchived metric is published."""
        record = {"body": json.dumps({"event_data": {}}), "messageId": "msg-metric"}
        with _mock_archiver_success_context(archiver_module, [record]):
            with patch.object(archiver_module, 'publish_metric') as mock_pub:
                with patch.object(archiver_module, 'count_results', return_value=(1, 0)):
                    archiver_module.lambda_handler(event={}, _context=lambda_context)
                    calls = mock_pub.call_args_list
                    archived_calls = [c for c in calls if "EventsArchived" in str(c)]
                    assert len(archived_calls) == 1

    def test_raises_runtime_error_on_failures(self, archiver_module, lambda_context):
        """Test that RuntimeError is raised when archiving fails."""
        record = {"body": "not json", "messageId": "msg-fail"}
        raised = False
        with patch.object(archiver_module, 'get_sqs_records', return_value=[record]):
            with patch.object(archiver_module, 'publish_metric'):
                with patch.object(archiver_module, 'count_results', return_value=(0, 1)):
                    with pytest.raises(RuntimeError):
                        archiver_module.lambda_handler(event={}, _context=lambda_context)
                    raised = True
        assert raised

    def test_publishes_archive_errors_metric_on_failure(self, archiver_module, lambda_context):
        """Test that ArchiveErrors metric is published on failure."""
        record = {"body": "not json", "messageId": "msg-error"}
        with patch.object(archiver_module, 'get_sqs_records', return_value=[record]):
            with patch.object(archiver_module, 'publish_metric') as mock_pub:
                with patch.object(archiver_module, 'count_results', return_value=(0, 1)):
                    try:
                        archiver_module.lambda_handler(event={}, _context=lambda_context)
                    except RuntimeError:
                        pass
                    error_calls = [c for c in mock_pub.call_args_list if "ArchiveErrors" in str(c)]
                    assert len(error_calls) == 1

    def test_publishes_processing_time_metric(self, archiver_module, lambda_context):
        """Test that ProcessingTime metric is published."""
        with patch.object(archiver_module, 'get_sqs_records', return_value=[]):
            with patch.object(archiver_module, 'publish_metric') as mock_pub:
                with patch.object(archiver_module, 'count_results', return_value=(0, 0)):
                    archiver_module.lambda_handler(event={}, _context=lambda_context)
                    calls = mock_pub.call_args_list
                    time_calls = [c for c in calls if "ProcessingTime" in str(c)]
                    assert len(time_calls) == 1
