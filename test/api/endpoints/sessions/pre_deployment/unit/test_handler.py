"""Unit tests for sessions Lambda handler."""
import os
from unittest.mock import patch

import pytest

from .conftest import create_mock_dynamodb


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
        mock_dynamodb = create_mock_dynamodb('batch_write_item', {})
        event = {
            'path': '/v1/sessions/abc123/events',
            'httpMethod': 'POST',
            'body': '{"device_id": "dev1", "events": [{"event_type": "test", "timestamp": "2024-01-15T10:30:00Z"}]}'
        }
        with patch.object(handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            response = handler.handle_events(event)
        assert response['statusCode'] == 200

    def test_valid_request_saves_events(self, handler):
        """Verify valid request saves events to DynamoDB."""
        mock_dynamodb = create_mock_dynamodb('batch_write_item', {})
        event = {
            'path': '/v1/sessions/abc123/events',
            'httpMethod': 'POST',
            'body': '{"device_id": "dev1", "events": [{"event_type": "test", "timestamp": "2024-01-15T10:30:00Z"}]}'
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
