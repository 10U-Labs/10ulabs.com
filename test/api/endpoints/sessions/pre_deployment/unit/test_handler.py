"""Unit tests for sessions Lambda handler."""
import base64
import json
import os
from unittest.mock import patch, MagicMock

import pytest
from botocore.exceptions import ClientError

from test_fixtures.unit import create_mock_dynamodb_client


class TestExtractSessionIdFromPath:
    """Tests for extract_session_id_from_path function."""

    def test_valid_path(self, handler):
        """Verify session_id is extracted from valid path."""
        result = handler.extract_session_id_from_path('/v1/sessions/abc123/events')
        assert result == 'abc123'

    def test_uuid_session_id(self, handler):
        """Verify UUID session_id is extracted correctly."""
        uuid = '550e8400-e29b-41d4-a716-446655440000'
        result = handler.extract_session_id_from_path(f'/v1/sessions/{uuid}/events')
        assert result == uuid

    def test_invalid_path_no_events(self, handler):
        """Verify None returned for path without /events suffix."""
        result = handler.extract_session_id_from_path('/v1/sessions/abc123')
        assert result is None

    def test_invalid_path_wrong_prefix(self, handler):
        """Verify None returned for path with wrong prefix."""
        result = handler.extract_session_id_from_path('/v2/sessions/abc123/events')
        assert result is None


class TestValidateAnalyticsEvent:
    """Tests for validate_analytics_event function."""

    def test_valid_event(self, handler):
        """Verify valid event passes validation."""
        event = {'event_type': 'page_view', 'timestamp': '2024-01-15T10:30:00Z'}
        result = handler.validate_analytics_event(event)
        assert result is None

    def test_missing_event_type(self, handler):
        """Verify missing event_type is caught."""
        event = {'timestamp': '2024-01-15T10:30:00Z'}
        result = handler.validate_analytics_event(event)
        assert 'event_type' in result

    def test_missing_timestamp(self, handler):
        """Verify missing timestamp is caught."""
        event = {'event_type': 'page_view'}
        result = handler.validate_analytics_event(event)
        assert 'timestamp' in result

    def test_invalid_timestamp_format(self, handler):
        """Verify invalid timestamp format is caught."""
        event = {'event_type': 'page_view', 'timestamp': 'not-a-timestamp'}
        result = handler.validate_analytics_event(event)
        assert 'ISO8601' in result


class TestValidateAnalyticsRequest:
    """Tests for validate_analytics_request function."""

    def test_valid_request(self, handler):
        """Verify valid request passes validation."""
        body = {
            'device_id': 'device123',
            'events': [{'event_type': 'test', 'timestamp': '2024-01-15T10:30:00Z'}]
        }
        result = handler.validate_analytics_request(body)
        assert result is None

    def test_missing_device_id(self, handler):
        """Verify missing device_id is caught."""
        body = {'events': [{'event_type': 'test', 'timestamp': '2024-01-15T10:30:00Z'}]}
        result = handler.validate_analytics_request(body)
        assert 'device_id' in result

    def test_missing_events(self, handler):
        """Verify missing events is caught."""
        body = {'device_id': 'device123'}
        result = handler.validate_analytics_request(body)
        assert 'events' in result

    def test_empty_events_array(self, handler):
        """Verify empty events array is caught."""
        body = {'device_id': 'device123', 'events': []}
        result = handler.validate_analytics_request(body)
        assert 'empty' in result

    def test_too_many_events(self, handler):
        """Verify more than 25 events is caught."""
        events = [{'event_type': 'test', 'timestamp': '2024-01-15T10:30:00Z'}] * 26
        body = {'device_id': 'device123', 'events': events}
        result = handler.validate_analytics_request(body)
        assert '25' in result


class TestHandleEvents:
    """Tests for handle_events function."""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """Set up environment variables for tests."""
        os.environ['SESSION_EVENTS_TABLE'] = 'test-events-table'
        yield
        del os.environ['SESSION_EVENTS_TABLE']

    def test_missing_session_id_returns_400(self, handler):
        """Verify missing session_id returns 400."""
        event = {
            'path': '/v1/sessions//events',
            'httpMethod': 'POST',
            'body': '{}'
        }
        response = handler.handle_events(event)
        assert response['statusCode'] == 400

    def test_missing_device_id_returns_400(self, handler):
        """Verify missing device_id returns 400."""
        event = {
            'path': '/v1/sessions/abc123/events',
            'httpMethod': 'POST',
            'body': '{"events": [{"event_type": "test", "timestamp": "2024-01-15T10:30:00Z"}]}'
        }
        response = handler.handle_events(event)
        assert response['statusCode'] == 400

    def test_invalid_event_returns_400(self, handler):
        """Verify invalid event in array returns 400."""
        event = {
            'path': '/v1/sessions/abc123/events',
            'httpMethod': 'POST',
            'body': '{"device_id": "dev1", "events": [{"event_type": "test"}]}'
        }
        response = handler.handle_events(event)
        assert response['statusCode'] == 400

    def test_valid_request_returns_200(self, handler):
        """Verify valid request returns 200."""
        mock_dynamodb = create_mock_dynamodb_client('batch_write_item', {})
        body = '{"device_id": "dev1", "events": [{"event_type": "test", ' \
               '"timestamp": "2024-01-15T10:30:00Z"}]}'
        event = {
            'path': '/v1/sessions/abc123/events',
            'httpMethod': 'POST',
            'body': body
        }
        with patch.object(handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            response = handler.handle_events(event)
        assert response['statusCode'] == 200

    def test_valid_request_saves_events(self, handler):
        """Verify valid request saves events to DynamoDB."""
        mock_dynamodb = create_mock_dynamodb_client('batch_write_item', {})
        body = '{"device_id": "dev1", "events": [{"event_type": "test", ' \
               '"timestamp": "2024-01-15T10:30:00Z"}]}'
        event = {
            'path': '/v1/sessions/abc123/events',
            'httpMethod': 'POST',
            'body': body
        }
        with patch.object(handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            handler.handle_events(event)
        mock_dynamodb.batch_write_item.assert_called_once()
        assert True  # Explicit pass


class TestLambdaHandler:
    """Tests for main lambda_handler function."""

    def test_options_returns_200(self, handler):
        """Verify OPTIONS request returns 200."""
        event = {'httpMethod': 'OPTIONS', 'path': '/v1/sessions/abc123/events'}
        response = handler.lambda_handler(event, None)
        assert response['statusCode'] == 200

    def test_options_returns_cors_headers(self, handler):
        """Verify OPTIONS request returns CORS headers."""
        event = {'httpMethod': 'OPTIONS', 'path': '/v1/sessions/abc123/events'}
        response = handler.lambda_handler(event, None)
        assert 'Access-Control-Allow-Origin' in response['headers']

    def test_unknown_path_returns_404(self, handler):
        """Verify unknown path returns 404."""
        event = {'httpMethod': 'GET', 'path': '/v1/unknown'}
        response = handler.lambda_handler(event, None)
        assert response['statusCode'] == 404


class TestParseBody:
    """Tests for parse_body function."""

    def test_returns_empty_dict_when_body_is_empty_string(self, handler):
        """Verify parse_body returns empty dict for empty string body."""
        event = {'body': ''}
        result = handler.parse_body(event)
        assert result == {}

    def test_returns_parsed_json_from_string_body(self, handler):
        """Verify parse_body parses JSON string body."""
        event = {'body': '{"key": "value"}'}
        result = handler.parse_body(event)
        assert result == {'key': 'value'}

    def test_handles_base64_encoded_body(self, handler):
        """Verify parse_body decodes base64 encoded body."""
        json_str = '{"device_id": "test123"}'
        encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        event = {'body': encoded, 'isBase64Encoded': True}
        result = handler.parse_body(event)
        assert result == {'device_id': 'test123'}


class TestValidateAnalyticsEventTypeChecks:
    """Tests for validate_analytics_event type validation."""

    def test_event_type_not_string_returns_error(self, handler):
        """Verify event_type must be a string."""
        event = {'event_type': 123, 'timestamp': '2024-01-15T10:30:00Z'}
        result = handler.validate_analytics_event(event)
        assert 'string' in result

    def test_timestamp_not_string_returns_error(self, handler):
        """Verify timestamp must be a string."""
        event = {'event_type': 'page_view', 'timestamp': 1234567890}
        result = handler.validate_analytics_event(event)
        assert 'string' in result


class TestValidateAnalyticsRequestTypeChecks:
    """Tests for validate_analytics_request type validation."""

    def test_device_id_not_string_returns_error(self, handler):
        """Verify device_id must be a string."""
        body = {
            'device_id': 12345,
            'events': [{'event_type': 'test', 'timestamp': '2024-01-15T10:30:00Z'}]
        }
        result = handler.validate_analytics_request(body)
        assert 'string' in result

    def test_events_not_array_returns_error(self, handler):
        """Verify events must be an array."""
        body = {
            'device_id': 'device123',
            'events': {'event_type': 'test', 'timestamp': '2024-01-15T10:30:00Z'}
        }
        result = handler.validate_analytics_request(body)
        assert 'array' in result


class TestJsonResponse:
    """Tests for json_response function."""

    def test_includes_content_type_header(self, handler):
        """Verify json_response includes Content-Type header."""
        response = handler.json_response(200, {'success': True})
        assert response['headers']['Content-Type'] == 'application/json'

    def test_includes_cors_allow_origin_header(self, handler):
        """Verify json_response includes CORS Allow-Origin header."""
        response = handler.json_response(200, {'success': True})
        assert response['headers']['Access-Control-Allow-Origin'] == '*'

    def test_includes_cors_allow_methods_header(self, handler):
        """Verify json_response includes CORS Allow-Methods header."""
        response = handler.json_response(200, {'success': True})
        assert 'GET' in response['headers']['Access-Control-Allow-Methods']
        assert 'POST' in response['headers']['Access-Control-Allow-Methods']

    def test_body_is_json_string(self, handler):
        """Verify json_response body is a JSON string."""
        response = handler.json_response(200, {'key': 'value'})
        parsed = json.loads(response['body'])
        assert parsed == {'key': 'value'}


class TestErrorResponse:
    """Tests for error_response function."""

    def test_includes_details_when_provided(self, handler):
        """Verify error_response includes details field when provided."""
        response = handler.error_response(400, 'Bad request', 'Missing field')
        body = json.loads(response['body'])
        assert body['details'] == 'Missing field'

    def test_excludes_details_when_empty(self, handler):
        """Verify error_response excludes details field when empty."""
        response = handler.error_response(400, 'Bad request', '')
        body = json.loads(response['body'])
        assert 'details' not in body

    def test_includes_success_false(self, handler):
        """Verify error_response includes success: false."""
        response = handler.error_response(400, 'Bad request')
        body = json.loads(response['body'])
        assert body['success'] is False


class TestSaveAnalyticsEvents:
    """Tests for save_analytics_events function."""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """Set up environment variables for tests."""
        os.environ['SESSION_EVENTS_TABLE'] = 'test-events-table'
        yield
        del os.environ['SESSION_EVENTS_TABLE']

    def test_includes_session_context_when_provided(self, handler):
        """Verify session_context is included in DynamoDB item."""
        mock_dynamodb = create_mock_dynamodb_client('batch_write_item', {})
        events = [{'event_type': 'test', 'timestamp': '2024-01-15T10:30:00Z'}]
        session_context = {'user_agent': 'TestBrowser/1.0'}
        with patch.object(handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            handler.save_analytics_events('session1', 'device1', events, session_context)
        call_args = mock_dynamodb.batch_write_item.call_args
        items = call_args[1]['RequestItems']['test-events-table']
        assert 'session_context' in items[0]['PutRequest']['Item']

    def test_returns_success_false_on_client_error(self, handler):
        """Verify ClientError returns success: false."""
        mock_dynamodb = MagicMock()
        error_response = {'Error': {'Code': 'ValidationException', 'Message': 'Error'}}
        mock_dynamodb.batch_write_item.side_effect = ClientError(error_response, 'BatchWriteItem')
        events = [{'event_type': 'test', 'timestamp': '2024-01-15T10:30:00Z'}]
        with patch.object(handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            result = handler.save_analytics_events('session1', 'device1', events, None)
        assert result['success'] is False

    def test_returns_events_saved_count_on_success(self, handler):
        """Verify success returns correct events_saved count."""
        mock_dynamodb = create_mock_dynamodb_client('batch_write_item', {})
        events = [
            {'event_type': 'test1', 'timestamp': '2024-01-15T10:30:00Z'},
            {'event_type': 'test2', 'timestamp': '2024-01-15T10:31:00Z'}
        ]
        with patch.object(handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            result = handler.save_analytics_events('session1', 'device1', events, None)
        assert result['events_saved'] == 2


class TestHandleEventsErrorHandling:
    """Tests for handle_events error handling."""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """Set up environment variables for tests."""
        os.environ['SESSION_EVENTS_TABLE'] = 'test-events-table'
        yield
        del os.environ['SESSION_EVENTS_TABLE']

    def test_dynamodb_error_returns_500(self, handler):
        """Verify DynamoDB ClientError returns 500."""
        mock_dynamodb = MagicMock()
        error_response = {'Error': {'Code': 'InternalError', 'Message': 'Error'}}
        mock_dynamodb.batch_write_item.side_effect = ClientError(error_response, 'BatchWriteItem')
        body = '{"device_id": "dev1", "events": [{"event_type": "test", ' \
               '"timestamp": "2024-01-15T10:30:00Z"}]}'
        event = {
            'path': '/v1/sessions/abc123/events',
            'httpMethod': 'POST',
            'body': body
        }
        with patch.object(handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            response = handler.handle_events(event)
        assert response['statusCode'] == 500
