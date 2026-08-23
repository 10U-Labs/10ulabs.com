"""Comprehensive tests for event_factories module."""
import json

from event_factories import (
    create_sqs_event,
    sqs_event_factory,
    create_dlq_message,
    dlq_message_factory,
)


# === create_sqs_event ===


class TestCreateSqsEvent:
    """Tests for create_sqs_event function."""

    def test_returns_dict(self):
        """create_sqs_event returns a dictionary."""
        result = create_sqs_event()
        assert isinstance(result, dict)

    def test_has_records_key(self):
        """create_sqs_event has Records key."""
        result = create_sqs_event()
        assert "Records" in result

    def test_default_has_one_record(self):
        """create_sqs_event default has one record."""
        result = create_sqs_event()
        assert len(result["Records"]) == 1

    def test_default_record_has_message_id(self):
        """create_sqs_event default record has messageId."""
        result = create_sqs_event()
        assert result["Records"][0]["messageId"] == "test-message-id"

    def test_default_record_has_body(self):
        """create_sqs_event default record has body."""
        result = create_sqs_event()
        body = json.loads(result["Records"][0]["body"])
        assert body["job_id"] == 123

    def test_custom_records(self):
        """create_sqs_event uses custom records."""
        custom = [{"messageId": "custom", "body": "{}"}]
        result = create_sqs_event(records=custom)
        assert result["Records"][0]["messageId"] == "custom"


# === sqs_event_factory ===


class TestSqsEventFactory:
    """Tests for sqs_event_factory function."""

    def test_returns_callable(self):
        """sqs_event_factory returns a callable."""
        factory = sqs_event_factory()
        assert callable(factory)

    def test_factory_creates_event(self):
        """sqs_event_factory creates valid events."""
        factory = sqs_event_factory()
        result = factory()
        assert "Records" in result


# === create_dlq_message ===


class TestCreateDlqMessage:
    """Tests for create_dlq_message function."""

    def test_returns_dict(self):
        """create_dlq_message returns a dictionary."""
        result = create_dlq_message()
        assert isinstance(result, dict)

    def test_has_message_id(self):
        """create_dlq_message has MessageId."""
        result = create_dlq_message()
        assert result["MessageId"] == "test-message-id"

    def test_has_receipt_handle(self):
        """create_dlq_message has ReceiptHandle."""
        result = create_dlq_message()
        assert result["ReceiptHandle"] == "test-receipt"

    def test_custom_receipt_handle(self):
        """create_dlq_message uses custom receipt_handle."""
        result = create_dlq_message(receipt_handle="custom-receipt")
        assert result["ReceiptHandle"] == "custom-receipt"

    def test_default_body(self):
        """create_dlq_message default body has job_id."""
        result = create_dlq_message()
        body = json.loads(result["Body"])
        assert body["job_id"] == 123

    def test_custom_body(self):
        """create_dlq_message uses custom body."""
        result = create_dlq_message(body={"custom": "data"})
        body = json.loads(result["Body"])
        assert body["custom"] == "data"

    def test_default_attributes(self):
        """create_dlq_message has default attributes."""
        result = create_dlq_message()
        assert result["Attributes"]["ApproximateReceiveCount"] == "1"

    def test_custom_attributes(self):
        """create_dlq_message uses custom attributes."""
        result = create_dlq_message(attributes={"Custom": "value"})
        assert result["Attributes"]["Custom"] == "value"


# === dlq_message_factory ===


class TestDlqMessageFactory:
    """Tests for dlq_message_factory function."""

    def test_returns_callable(self):
        """dlq_message_factory returns a callable."""
        factory = dlq_message_factory()
        assert callable(factory)

    def test_factory_creates_message(self):
        """dlq_message_factory creates valid messages."""
        factory = dlq_message_factory()
        result = factory()
        assert "MessageId" in result
