"""Unit tests for audit_logger module."""
import json
from unittest.mock import MagicMock, patch

import pytest

from audit_logger import (
    AuditRecord,
    WriteAheadLogger,
    audit_request,
    redact_payload,
    DEFAULT_REDACT_FIELDS,
)


class TestRedactPayload:
    """Tests for redact_payload function."""

    def test_redacts_password_field(self):
        """Test password field is redacted."""
        payload = {'username': 'user', 'password': 'secret123'}
        result = redact_payload(payload)
        assert result['password'] == '[REDACTED]'

    def test_preserves_non_password_field(self):
        """Test non-password field is preserved."""
        payload = {'username': 'user', 'password': 'secret123'}
        result = redact_payload(payload)
        assert result['username'] == 'user'

    def test_redacts_token_field(self):
        """Test token field is redacted."""
        payload = {'token': 'abc123', 'data': 'value'}
        result = redact_payload(payload)
        assert result['token'] == '[REDACTED]'

    def test_redacts_nested_api_key(self):
        """Test nested api_key field is redacted."""
        payload = {'user': {'name': 'test', 'api_key': 'key123'}}
        result = redact_payload(payload)
        assert result['user']['api_key'] == '[REDACTED]'

    def test_preserves_nested_name(self):
        """Test nested name field is preserved."""
        payload = {'user': {'name': 'test', 'api_key': 'key123'}}
        result = redact_payload(payload)
        assert result['user']['name'] == 'test'

    def test_redacts_password_in_array(self):
        """Test password in array is redacted."""
        payload = {'users': [{'name': 'user1', 'password': 'pass1'}]}
        result = redact_payload(payload)
        assert result['users'][0]['password'] == '[REDACTED]'

    def test_uppercase_password_redacted(self):
        """Test uppercase PASSWORD is redacted (case-insensitive)."""
        payload = {'PASSWORD': 'secret'}
        result = redact_payload(payload)
        assert result['PASSWORD'] == '[REDACTED]'

    def test_mixed_case_token_redacted(self):
        """Test mixed case Token is redacted."""
        payload = {'Token': 'abc'}
        result = redact_payload(payload)
        assert result['Token'] == '[REDACTED]'

    def test_custom_redact_field(self):
        """Test custom redact field works."""
        payload = {'email': 'user@test.com', 'name': 'test'}
        result = redact_payload(payload, redact_fields=['email'])
        assert result['email'] == '[REDACTED]'

    def test_preserves_non_sensitive_data(self):
        """Test non-sensitive data is preserved."""
        payload = {'action': 'queued', 'job_id': 123}
        result = redact_payload(payload)
        assert result == payload

    def test_handles_empty_payload(self):
        """Test empty payload returns empty dict."""
        result = redact_payload({})
        assert result == {}

    def test_handles_string_primitive(self):
        """Test string primitive is returned as-is."""
        assert redact_payload('string') == 'string'

    def test_handles_int_primitive(self):
        """Test int primitive is returned as-is."""
        assert redact_payload(123) == 123

    def test_handles_none_primitive(self):
        """Test None is returned as-is."""
        assert redact_payload(None) is None


class TestAuditRecord:
    """Tests for AuditRecord dataclass."""

    def test_request_id_set(self):
        """Test request_id is set correctly."""
        record = AuditRecord(
            request_id='test-123', endpoint='test', method='POST',
            status='received', request_timestamp='2024-01-01T00:00:00Z'
        )
        assert record.request_id == 'test-123'

    def test_endpoint_set(self):
        """Test endpoint is set correctly."""
        record = AuditRecord(
            request_id='test-123', endpoint='test-endpoint', method='POST',
            status='received', request_timestamp='2024-01-01T00:00:00Z'
        )
        assert record.endpoint == 'test-endpoint'

    def test_method_set(self):
        """Test method is set correctly."""
        record = AuditRecord(
            request_id='test-123', endpoint='test', method='POST',
            status='received', request_timestamp='2024-01-01T00:00:00Z'
        )
        assert record.method == 'POST'

    def test_status_set(self):
        """Test status is set correctly."""
        record = AuditRecord(
            request_id='test-123', endpoint='test', method='POST',
            status='received', request_timestamp='2024-01-01T00:00:00Z'
        )
        assert record.status == 'received'

    def test_ttl_calculates_90_days(self):
        """Test TTL is 90 days from request timestamp."""
        record = AuditRecord(
            request_id='test-123', endpoint='test', method='POST',
            status='received', request_timestamp='2024-01-01T00:00:00Z'
        )
        expected_base = 1704067200
        expected_ttl = expected_base + (90 * 24 * 60 * 60)
        assert record.ttl == expected_ttl

    def test_ttl_handles_invalid_timestamp(self):
        """Test TTL fallback for invalid timestamp."""
        record = AuditRecord(
            request_id='test-123', endpoint='test', method='POST',
            status='received', request_timestamp='invalid'
        )
        assert record.ttl > 0

    def test_endpoint_timestamp_format(self):
        """Test endpoint_timestamp property format."""
        record = AuditRecord(
            request_id='test-123', endpoint='my-endpoint', method='POST',
            status='received', request_timestamp='2024-01-01T00:00:00Z'
        )
        assert record.endpoint_timestamp == 'my-endpoint#2024-01-01T00:00:00Z'


class TestWriteAheadLogger:
    """Tests for WriteAheadLogger class."""

    @pytest.fixture
    def logger(self):
        """Create a WriteAheadLogger instance."""
        return WriteAheadLogger(
            audit_table_name='test-audit-table',
            write_ahead_queue_url='https://sqs.test.com/queue',
            endpoint_name='test-endpoint'
        )

    @pytest.fixture
    def mock_event(self):
        """Create a mock Lambda event."""
        return {
            'httpMethod': 'POST',
            'headers': {'user-agent': 'test-agent', 'x-correlation-id': 'corr-123'},
            'requestContext': {'http': {'sourceIp': '1.2.3.4'}},
            'body': json.dumps({'action': 'test', 'token': 'secret'})
        }

    def test_extracts_method(self, logger, mock_event):
        """Test _extract_request_info extracts method."""
        result = logger.extract_request_info(mock_event)
        assert result['method'] == 'POST'

    def test_extracts_user_agent(self, logger, mock_event):
        """Test _extract_request_info extracts user_agent."""
        result = logger.extract_request_info(mock_event)
        assert result['user_agent'] == 'test-agent'

    def test_extracts_correlation_id(self, logger, mock_event):
        """Test _extract_request_info extracts correlation_id."""
        result = logger.extract_request_info(mock_event)
        assert result['correlation_id'] == 'corr-123'

    def test_parses_json_body(self, logger):
        """Test _parse_body parses JSON correctly."""
        event = {'body': json.dumps({'key': 'value'})}
        result = logger.parse_body(event)
        assert result == {'key': 'value'}

    def test_parses_empty_body(self, logger):
        """Test _parse_body handles empty body."""
        event = {'body': ''}
        result = logger.parse_body(event)
        assert result == {}

    def test_parses_invalid_json_returns_raw(self, logger):
        """Test _parse_body returns truncated raw for invalid JSON."""
        event = {'body': 'not json'}
        result = logger.parse_body(event)
        assert '_raw' in result

    @patch('audit_logger._get_dynamodb_client')
    @patch('audit_logger._get_sqs_client')
    def test_log_request_received_sets_endpoint(self, mock_sqs, mock_ddb, logger, mock_event):
        """Test log_request_received sets endpoint correctly."""
        mock_sqs.return_value = MagicMock()
        mock_ddb.return_value = MagicMock()
        record = logger.log_request_received(mock_event)
        assert record.endpoint == 'test-endpoint'

    @patch('audit_logger._get_dynamodb_client')
    @patch('audit_logger._get_sqs_client')
    def test_log_request_received_sets_status_received(
        self, mock_sqs, mock_ddb, logger, mock_event
    ):
        """Test log_request_received sets status to received."""
        mock_sqs.return_value = MagicMock()
        mock_ddb.return_value = MagicMock()
        record = logger.log_request_received(mock_event)
        assert record.status == 'received'

    @patch('audit_logger._get_dynamodb_client')
    def test_log_processing_started_updates_status(self, mock_dynamodb, logger):
        """Test log_processing_started updates record status."""
        mock_dynamodb.return_value = MagicMock()
        record = AuditRecord(
            request_id='test-123', endpoint='test', method='POST',
            status='received', request_timestamp='2024-01-01T00:00:00Z'
        )
        logger.log_processing_started(record)
        assert record.status == 'processing'

    @patch('audit_logger._get_dynamodb_client')
    def test_log_completed_updates_status(self, mock_dynamodb, logger):
        """Test log_completed updates status."""
        mock_dynamodb.return_value = MagicMock()
        record = AuditRecord(
            request_id='test-123', endpoint='test', method='POST',
            status='processing', request_timestamp='2024-01-01T00:00:00Z'
        )
        logger.log_completed(record, 200)
        assert record.status == 'completed'

    @patch('audit_logger._get_dynamodb_client')
    def test_log_completed_sets_response_code(self, mock_dynamodb, logger):
        """Test log_completed sets response code."""
        mock_dynamodb.return_value = MagicMock()
        record = AuditRecord(
            request_id='test-123', endpoint='test', method='POST',
            status='processing', request_timestamp='2024-01-01T00:00:00Z'
        )
        logger.log_completed(record, 200)
        assert record.response_code == 200

    @patch('audit_logger._get_dynamodb_client')
    def test_log_failed_updates_status(self, mock_dynamodb, logger):
        """Test log_failed updates status."""
        mock_dynamodb.return_value = MagicMock()
        record = AuditRecord(
            request_id='test-123', endpoint='test', method='POST',
            status='processing', request_timestamp='2024-01-01T00:00:00Z'
        )
        logger.log_failed(record, 'Test error', 500)
        assert record.status == 'failed'

    @patch('audit_logger._get_dynamodb_client')
    def test_log_failed_sets_error_message(self, mock_dynamodb, logger):
        """Test log_failed sets error message."""
        mock_dynamodb.return_value = MagicMock()
        record = AuditRecord(
            request_id='test-123', endpoint='test', method='POST',
            status='processing', request_timestamp='2024-01-01T00:00:00Z'
        )
        logger.log_failed(record, 'Test error', 500)
        assert record.error_message == 'Test error'


class TestAuditRequestDecorator:
    """Tests for audit_request decorator."""

    @patch('audit_logger._get_dynamodb_client')
    @patch('audit_logger._get_sqs_client')
    def test_decorator_returns_handler_response(self, mock_sqs, mock_dynamodb):
        """Test decorator returns handler response."""
        mock_sqs.return_value = MagicMock()
        mock_dynamodb.return_value = MagicMock()

        @audit_request('test-endpoint')
        def handler(_event, _context):
            return {'statusCode': 200, 'body': 'success'}

        event = {'httpMethod': 'POST', 'headers': {}, 'body': '{}'}
        with patch.dict('os.environ', {'AUDIT_ENABLED': 'true', 'AUDIT_TABLE_NAME': 'test'}):
            result = handler(event, None)
        assert result['statusCode'] == 200

    def test_decorator_disabled_when_audit_disabled(self):
        """Test decorator is bypassed when AUDIT_ENABLED is false."""
        @audit_request('test-endpoint')
        def handler(_event, _context):
            return {'statusCode': 200, 'body': 'success'}

        event = {'httpMethod': 'POST', 'headers': {}, 'body': '{}'}
        with patch.dict('os.environ', {'AUDIT_ENABLED': 'false'}, clear=True):
            result = handler(event, None)
        assert result['statusCode'] == 200

    def test_decorator_disabled_when_no_table(self):
        """Test decorator is bypassed when AUDIT_TABLE_NAME is not set."""
        @audit_request('test-endpoint')
        def handler(_event, _context):
            return {'statusCode': 200, 'body': 'success'}

        event = {'httpMethod': 'POST', 'headers': {}, 'body': '{}'}
        with patch.dict('os.environ', {'AUDIT_ENABLED': 'true'}, clear=True):
            result = handler(event, None)
        assert result['statusCode'] == 200


class TestDefaultRedactFields:
    """Tests for default redact fields configuration."""

    def test_default_fields_include_password(self):
        """Test password is in default redact fields."""
        assert 'password' in DEFAULT_REDACT_FIELDS

    def test_default_fields_include_token(self):
        """Test token is in default redact fields."""
        assert 'token' in DEFAULT_REDACT_FIELDS

    def test_default_fields_include_api_key(self):
        """Test api_key is in default redact fields."""
        assert 'api_key' in DEFAULT_REDACT_FIELDS

    def test_default_fields_include_github_token(self):
        """Test github_token is in default redact fields."""
        assert 'github_token' in DEFAULT_REDACT_FIELDS

    def test_default_fields_include_webhook_secret(self):
        """Test webhook_secret is in default redact fields."""
        assert 'webhook_secret' in DEFAULT_REDACT_FIELDS
