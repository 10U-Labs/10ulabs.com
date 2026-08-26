import json

from event_factories import (
    create_sqs_event,
    sqs_event_factory,
    create_dlq_message,
    dlq_message_factory,
)


class TestCreateSqsEvent:
    def test_returns_dict(self):
        result = create_sqs_event()
        assert isinstance(result, dict)

    def test_has_records_key(self):
        result = create_sqs_event()
        assert "Records" in result

    def test_default_has_one_record(self):
        result = create_sqs_event()
        assert len(result["Records"]) == 1

    def test_default_record_has_message_id(self):
        result = create_sqs_event()
        assert result["Records"][0]["messageId"] == "test-message-id"

    def test_default_record_has_body(self):
        result = create_sqs_event()
        body = json.loads(result["Records"][0]["body"])
        assert body["job_id"] == 123

    def test_custom_records(self):
        custom = [{"messageId": "custom", "body": "{}"}]
        result = create_sqs_event(records=custom)
        assert result["Records"][0]["messageId"] == "custom"


class TestSqsEventFactory:
    def test_returns_callable(self):
        factory = sqs_event_factory()
        assert callable(factory)

    def test_factory_creates_event(self):
        factory = sqs_event_factory()
        result = factory()
        assert "Records" in result


class TestCreateDlqMessage:
    def test_returns_dict(self):
        result = create_dlq_message()
        assert isinstance(result, dict)

    def test_has_message_id(self):
        result = create_dlq_message()
        assert result["MessageId"] == "test-message-id"

    def test_has_receipt_handle(self):
        result = create_dlq_message()
        assert result["ReceiptHandle"] == "test-receipt"

    def test_custom_receipt_handle(self):
        result = create_dlq_message(receipt_handle="custom-receipt")
        assert result["ReceiptHandle"] == "custom-receipt"

    def test_default_body(self):
        result = create_dlq_message()
        body = json.loads(result["Body"])
        assert body["job_id"] == 123

    def test_custom_body(self):
        result = create_dlq_message(body={"custom": "data"})
        body = json.loads(result["Body"])
        assert body["custom"] == "data"

    def test_default_attributes(self):
        result = create_dlq_message()
        assert result["Attributes"]["ApproximateReceiveCount"] == "1"

    def test_custom_attributes(self):
        result = create_dlq_message(attributes={"Custom": "value"})
        assert result["Attributes"]["Custom"] == "value"


class TestDlqMessageFactory:
    def test_returns_callable(self):
        factory = dlq_message_factory()
        assert callable(factory)

    def test_factory_creates_message(self):
        factory = dlq_message_factory()
        result = factory()
        assert "MessageId" in result
