import base64
import json
import os
from types import ModuleType
from typing import Any, Dict, Iterator
from unittest.mock import patch, MagicMock

import pytest
from botocore.exceptions import ClientError

from test_fixtures.unit import create_mock_dynamodb_client, reset_module_state


def _one_event_post_request() -> Dict[str, Any]:
    return {
        'path': '/v1/sessions/abc123/events',
        'httpMethod': 'POST',
        'body': '{"device_id": "dev1", "events": [{"event_type": "test", '
                '"timestamp": "2024-01-15T10:30:00Z"}]}'
    }


class TestExtractSessionIdFromPath:
    def test_valid_path(self, handler: ModuleType) -> None:
        result = handler.extract_session_id_from_path('/v1/sessions/abc123/events')
        assert result == 'abc123'

    def test_uuid_session_id(self, handler: ModuleType) -> None:
        uuid = '550e8400-e29b-41d4-a716-446655440000'
        result = handler.extract_session_id_from_path(f'/v1/sessions/{uuid}/events')
        assert result == uuid

    def test_invalid_path_no_events(self, handler: ModuleType) -> None:
        result = handler.extract_session_id_from_path('/v1/sessions/abc123')
        assert result is None

    def test_invalid_path_wrong_prefix(self, handler: ModuleType) -> None:
        result = handler.extract_session_id_from_path('/v2/sessions/abc123/events')
        assert result is None


class TestValidateAnalyticsEvent:
    def test_valid_event(self, handler: ModuleType) -> None:
        event = {'event_type': 'page_view', 'timestamp': '2024-01-15T10:30:00Z'}
        result = handler.validate_analytics_event(event)
        assert result is None

    def test_missing_event_type(self, handler: ModuleType) -> None:
        event = {'timestamp': '2024-01-15T10:30:00Z'}
        result = handler.validate_analytics_event(event)
        assert 'event_type' in result

    def test_missing_timestamp(self, handler: ModuleType) -> None:
        event = {'event_type': 'page_view'}
        result = handler.validate_analytics_event(event)
        assert 'timestamp' in result

    def test_invalid_timestamp_format(self, handler: ModuleType) -> None:
        event = {'event_type': 'page_view', 'timestamp': 'not-a-timestamp'}
        result = handler.validate_analytics_event(event)
        assert 'ISO8601' in result


class TestValidateAnalyticsRequest:
    def test_valid_request(self, handler: ModuleType) -> None:
        body = {
            'device_id': 'device123',
            'events': [{'event_type': 'test', 'timestamp': '2024-01-15T10:30:00Z'}]
        }
        result = handler.validate_analytics_request(body)
        assert result is None

    def test_missing_device_id(self, handler: ModuleType) -> None:
        body = {'events': [{'event_type': 'test', 'timestamp': '2024-01-15T10:30:00Z'}]}
        result = handler.validate_analytics_request(body)
        assert 'device_id' in result

    def test_missing_events(self, handler: ModuleType) -> None:
        body = {'device_id': 'device123'}
        result = handler.validate_analytics_request(body)
        assert 'events' in result

    def test_empty_events_array(self, handler: ModuleType) -> None:
        body = {'device_id': 'device123', 'events': []}
        result = handler.validate_analytics_request(body)
        assert 'empty' in result

    def test_too_many_events(self, handler: ModuleType) -> None:
        events = [{'event_type': 'test', 'timestamp': '2024-01-15T10:30:00Z'}] * 26
        body = {'device_id': 'device123', 'events': events}
        result = handler.validate_analytics_request(body)
        assert '25' in result


class TestHandleEvents:
    @pytest.fixture(autouse=True)
    def setup_env(self) -> Iterator[None]:
        os.environ['SESSION_EVENTS_TABLE'] = 'test-events-table'
        yield
        del os.environ['SESSION_EVENTS_TABLE']

    def test_missing_session_id_returns_400(self, handler: ModuleType) -> None:
        event = {
            'path': '/v1/sessions//events',
            'httpMethod': 'POST',
            'body': '{}'
        }
        response = handler.handle_events(event)
        assert response['statusCode'] == 400

    def test_missing_device_id_returns_400(self, handler: ModuleType) -> None:
        event = {
            'path': '/v1/sessions/abc123/events',
            'httpMethod': 'POST',
            'body': '{"events": [{"event_type": "test", "timestamp": "2024-01-15T10:30:00Z"}]}'
        }
        response = handler.handle_events(event)
        assert response['statusCode'] == 400

    def test_invalid_event_returns_400(self, handler: ModuleType) -> None:
        event = {
            'path': '/v1/sessions/abc123/events',
            'httpMethod': 'POST',
            'body': '{"device_id": "dev1", "events": [{"event_type": "test"}]}'
        }
        response = handler.handle_events(event)
        assert response['statusCode'] == 400

    def test_valid_request_returns_200(self, handler: ModuleType) -> None:
        mock_dynamodb = create_mock_dynamodb_client('batch_write_item', {})
        event = _one_event_post_request()
        with patch.object(handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            response = handler.handle_events(event)
        assert response['statusCode'] == 200

    def test_valid_request_saves_events(self, handler: ModuleType) -> None:
        mock_dynamodb = create_mock_dynamodb_client('batch_write_item', {})
        event = _one_event_post_request()
        with patch.object(handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            handler.handle_events(event)
        mock_dynamodb.batch_write_item.assert_called_once()
        assert True


class TestLambdaHandler:
    def test_options_returns_200(self, handler: ModuleType) -> None:
        event = {'httpMethod': 'OPTIONS', 'path': '/v1/sessions/abc123/events'}
        response = handler.lambda_handler(event, None)
        assert response['statusCode'] == 200

    def test_options_returns_cors_headers(self, handler: ModuleType) -> None:
        event = {'httpMethod': 'OPTIONS', 'path': '/v1/sessions/abc123/events'}
        response = handler.lambda_handler(event, None)
        assert 'Access-Control-Allow-Origin' in response['headers']

    def test_unknown_path_returns_404(self, handler: ModuleType) -> None:
        event = {'httpMethod': 'GET', 'path': '/v1/unknown'}
        response = handler.lambda_handler(event, None)
        assert response['statusCode'] == 404


class TestParseBody:
    def test_returns_empty_dict_when_body_is_empty_string(self, handler: ModuleType) -> None:
        event = {'body': ''}
        result = handler.parse_body(event)
        assert result == {}

    def test_returns_parsed_json_from_string_body(self, handler: ModuleType) -> None:
        event = {'body': '{"key": "value"}'}
        result = handler.parse_body(event)
        assert result == {'key': 'value'}

    def test_handles_base64_encoded_body(self, handler: ModuleType) -> None:
        json_str = '{"device_id": "test123"}'
        encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        event = {'body': encoded, 'isBase64Encoded': True}
        result = handler.parse_body(event)
        assert result == {'device_id': 'test123'}


class TestValidateAnalyticsEventTypeChecks:
    def test_event_type_not_string_returns_error(self, handler: ModuleType) -> None:
        event = {'event_type': 123, 'timestamp': '2024-01-15T10:30:00Z'}
        result = handler.validate_analytics_event(event)
        assert 'string' in result

    def test_timestamp_not_string_returns_error(self, handler: ModuleType) -> None:
        event = {'event_type': 'page_view', 'timestamp': 1234567890}
        result = handler.validate_analytics_event(event)
        assert 'string' in result


class TestValidateAnalyticsRequestTypeChecks:
    def test_device_id_not_string_returns_error(self, handler: ModuleType) -> None:
        body = {
            'device_id': 12345,
            'events': [{'event_type': 'test', 'timestamp': '2024-01-15T10:30:00Z'}]
        }
        result = handler.validate_analytics_request(body)
        assert 'string' in result

    def test_events_not_array_returns_error(self, handler: ModuleType) -> None:
        body = {
            'device_id': 'device123',
            'events': {'event_type': 'test', 'timestamp': '2024-01-15T10:30:00Z'}
        }
        result = handler.validate_analytics_request(body)
        assert 'array' in result


class TestJsonResponse:
    def test_includes_content_type_header(self, handler: ModuleType) -> None:
        response = handler.json_response(200, {'success': True})
        assert response['headers']['Content-Type'] == 'application/json'

    def test_includes_cors_allow_origin_header(self, handler: ModuleType) -> None:
        response = handler.json_response(200, {'success': True})
        assert response['headers']['Access-Control-Allow-Origin'] == '*'

    def test_includes_cors_allow_methods_get(self, handler: ModuleType) -> None:
        response = handler.json_response(200, {'success': True})
        assert 'GET' in response['headers']['Access-Control-Allow-Methods']

    def test_includes_cors_allow_methods_post(self, handler: ModuleType) -> None:
        response = handler.json_response(200, {'success': True})
        assert 'POST' in response['headers']['Access-Control-Allow-Methods']

    def test_body_is_json_string(self, handler: ModuleType) -> None:
        response = handler.json_response(200, {'key': 'value'})
        parsed = json.loads(response['body'])
        assert parsed == {'key': 'value'}


class TestErrorResponse:
    def test_includes_details_when_provided(self, handler: ModuleType) -> None:
        response = handler.error_response(400, 'Bad request', 'Missing field')
        body = json.loads(response['body'])
        assert body['details'] == 'Missing field'

    def test_excludes_details_when_empty(self, handler: ModuleType) -> None:
        response = handler.error_response(400, 'Bad request', '')
        body = json.loads(response['body'])
        assert 'details' not in body

    def test_includes_success_false(self, handler: ModuleType) -> None:
        response = handler.error_response(400, 'Bad request')
        body = json.loads(response['body'])
        assert body['success'] is False


class TestSaveAnalyticsEvents:
    @pytest.fixture(autouse=True)
    def setup_env(self) -> Iterator[None]:
        os.environ['SESSION_EVENTS_TABLE'] = 'test-events-table'
        yield
        del os.environ['SESSION_EVENTS_TABLE']

    def test_includes_session_context_when_provided(self, handler: ModuleType) -> None:
        mock_dynamodb = create_mock_dynamodb_client('batch_write_item', {})
        events = [{'event_type': 'test', 'timestamp': '2024-01-15T10:30:00Z'}]
        session_context = {'user_agent': 'TestBrowser/1.0'}
        with patch.object(handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            handler.save_analytics_events('session1', 'device1', events, session_context)
        call_args = mock_dynamodb.batch_write_item.call_args
        items = call_args[1]['RequestItems']['test-events-table']
        assert 'session_context' in items[0]['PutRequest']['Item']

    def test_returns_success_false_on_client_error(self, handler: ModuleType) -> None:
        mock_dynamodb = MagicMock()
        error_response = {'Error': {'Code': 'ValidationException', 'Message': 'Error'}}
        mock_dynamodb.batch_write_item.side_effect = ClientError(error_response, 'BatchWriteItem')
        events = [{'event_type': 'test', 'timestamp': '2024-01-15T10:30:00Z'}]
        with patch.object(handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            result = handler.save_analytics_events('session1', 'device1', events, None)
        assert result['success'] is False

    def test_returns_events_saved_count_on_success(self, handler: ModuleType) -> None:
        mock_dynamodb = create_mock_dynamodb_client('batch_write_item', {})
        events = [
            {'event_type': 'test1', 'timestamp': '2024-01-15T10:30:00Z'},
            {'event_type': 'test2', 'timestamp': '2024-01-15T10:31:00Z'}
        ]
        with patch.object(handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            result = handler.save_analytics_events('session1', 'device1', events, None)
        assert result['events_saved'] == 2


class TestHandleEventsErrorHandling:
    @pytest.fixture(autouse=True)
    def setup_env(self) -> Iterator[None]:
        os.environ['SESSION_EVENTS_TABLE'] = 'test-events-table'
        yield
        del os.environ['SESSION_EVENTS_TABLE']

    def test_dynamodb_error_returns_500(self, handler: ModuleType) -> None:
        mock_dynamodb = MagicMock()
        error_response = {'Error': {'Code': 'InternalError', 'Message': 'Error'}}
        mock_dynamodb.batch_write_item.side_effect = ClientError(error_response, 'BatchWriteItem')
        event = _one_event_post_request()
        with patch.object(handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            response = handler.handle_events(event)
        assert response['statusCode'] == 500

    def test_value_error_returns_500(self, handler: ModuleType) -> None:
        event = {
            'path': '/v1/sessions/abc123/events',
            'httpMethod': 'POST',
            'body': 'invalid json {'
        }
        response = handler.handle_events(event)
        assert response['statusCode'] == 500

    def test_key_error_returns_500(self, handler: ModuleType) -> None:
        mock_dynamodb = create_mock_dynamodb_client('batch_write_item', {})
        event = {
            'path': '/v1/sessions/abc123/events',
            'httpMethod': 'POST',
            'body': (
                '{"device_id": "dev1", "events": [{"event_type": "test",'
                ' "timestamp": "2024-01-15T10:30:00Z"}]}'
            )
        }
        with patch.object(handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            with patch.object(
                handler, 'save_analytics_events',
                side_effect=KeyError('missing_key')
            ):
                response = handler.handle_events(event)
        assert response['statusCode'] == 500


class TestGetDynamoDbClient:
    def test_creates_client_when_not_cached(self, handler: ModuleType) -> None:
        reset_module_state(handler, _clients={})
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            result = handler.get_dynamodb_client()
            mock_boto.assert_called_once_with('dynamodb')
            assert result == mock_client

    def test_returns_cached_client(self, handler: ModuleType) -> None:
        reset_module_state(handler, _clients={})
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            first_result = handler.get_dynamodb_client()
            second_result = handler.get_dynamodb_client()
            mock_boto.assert_called_once()
            assert first_result == second_result


class TestLambdaHandlerPostRoute:
    @pytest.fixture(autouse=True)
    def setup_env(self) -> Iterator[None]:
        os.environ['SESSION_EVENTS_TABLE'] = 'test-events-table'
        yield
        del os.environ['SESSION_EVENTS_TABLE']

    def test_post_to_events_endpoint_routes_to_handle_events(self, handler: ModuleType) -> None:
        mock_dynamodb = create_mock_dynamodb_client('batch_write_item', {})
        event = {
            'httpMethod': 'POST',
            'path': '/v1/sessions/test-session/events',
            'body': (
                '{"device_id": "dev1", "events": [{"event_type": "test",'
                ' "timestamp": "2024-01-15T10:30:00Z"}]}'
            )
        }
        with patch.object(handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            response = handler.lambda_handler(event, None)
        assert response['statusCode'] == 200

    def test_post_to_events_returns_success(self, handler: ModuleType) -> None:
        mock_dynamodb = create_mock_dynamodb_client('batch_write_item', {})
        event = {
            'httpMethod': 'POST',
            'path': '/v1/sessions/my-session-id/events',
            'body': (
                '{"device_id": "device123", "events": [{"event_type":'
                ' "click", "timestamp": "2024-01-15T10:30:00Z"}]}'
            )
        }
        with patch.object(handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            response = handler.lambda_handler(event, None)
        body = json.loads(response['body'])
        assert body['success'] is True
