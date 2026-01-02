"""Unit tests for rack designer analytics event handler."""
import json
from unittest.mock import patch

from .conftest import create_mock_dynamodb


def test_handle_events_missing_session_id_in_path(handler):
    """Test handle_events returns 400 without session_id in path."""
    body = json.dumps({'device_id': 'abc', 'events': [{'event_type': 'test', 'timestamp': '2025-01-01T00:00:00Z'}]})
    event = {'body': body, 'headers': {}, 'path': '/v1/sessions//events'}
    response = handler.handle_events(event)
    assert response['statusCode'] == 400


def test_handle_events_missing_device_id(handler):
    """Test handle_events returns 400 without device_id."""
    body = json.dumps({'events': [{'event_type': 'test', 'timestamp': '2025-01-01T00:00:00Z'}]})
    event = {'body': body, 'headers': {}, 'path': '/v1/sessions/abc/events'}
    response = handler.handle_events(event)
    assert response['statusCode'] == 400


def test_handle_events_missing_events_array(handler):
    """Test handle_events returns 400 without events array."""
    body = json.dumps({'device_id': 'def'})
    event = {'body': body, 'headers': {}, 'path': '/v1/sessions/abc/events'}
    response = handler.handle_events(event)
    assert response['statusCode'] == 400


def test_handle_events_empty_events_array(handler):
    """Test handle_events returns 400 for empty events array."""
    body = json.dumps({'device_id': 'def', 'events': []})
    event = {'body': body, 'headers': {}, 'path': '/v1/sessions/abc/events'}
    response = handler.handle_events(event)
    assert response['statusCode'] == 400


def test_handle_events_too_many_events(handler):
    """Test handle_events returns 400 for too many events."""
    events = [{'event_type': 'test', 'timestamp': '2025-01-01T00:00:00Z'}] * 26
    body = json.dumps({'device_id': 'def', 'events': events})
    event = {'body': body, 'headers': {}, 'path': '/v1/sessions/abc/events'}
    response = handler.handle_events(event)
    assert response['statusCode'] == 400


def _create_events_request(events_list, session_context=None):
    """Create an events request body for testing."""
    payload = {'device_id': 'def', 'events': events_list}
    if session_context:
        payload['session_context'] = session_context
    return {'body': json.dumps(payload), 'headers': {}, 'path': '/v1/sessions/abc/events'}


def test_handle_events_invalid_event_missing_type(handler):
    """Test handle_events returns 400 for event missing type."""
    events_with_missing_type = [{'timestamp': '2025-01-01T00:00:00Z'}]
    event = _create_events_request(events_with_missing_type)
    response = handler.handle_events(event)
    assert response['statusCode'] == 400


def test_handle_events_invalid_event_missing_timestamp(handler):
    """Test handle_events returns 400 for event missing timestamp."""
    events_with_missing_ts = [{'event_type': 'test'}]
    event = _create_events_request(events_with_missing_ts)
    response = handler.handle_events(event)
    assert response['statusCode'] == 400


@patch('boto3.client')
def test_handle_events_success_single_event(mock_boto_client, handler):
    """Test handle_events returns 200 for single valid event."""
    mock_boto_client.return_value = create_mock_dynamodb('batch_write_item')
    handler.clear_clients()
    events = [{'event_type': 'test', 'timestamp': '2025-01-01T00:00:00Z'}]
    event = _create_events_request(events)
    with patch.dict('os.environ', {'RACK_DESIGNER_EVENTS_TABLE': 'test-events-table'}):
        response = handler.handle_events(event)
    assert response['statusCode'] == 200


@patch('boto3.client')
def test_handle_events_success_multiple_events(mock_boto_client, handler):
    """Test handle_events returns 200 for multiple valid events."""
    mock_boto_client.return_value = create_mock_dynamodb('batch_write_item')
    handler.clear_clients()
    events = [
        {'event_type': 'test1', 'timestamp': '2025-01-01T00:00:00Z'},
        {'event_type': 'test2', 'timestamp': '2025-01-01T00:00:01Z'}
    ]
    event = _create_events_request(events)
    with patch.dict('os.environ', {'RACK_DESIGNER_EVENTS_TABLE': 'test-events-table'}):
        response = handler.handle_events(event)
    assert response['statusCode'] == 200


@patch('boto3.client')
def test_handle_events_with_session_context(mock_boto_client, handler):
    """Test handle_events handles session context correctly."""
    mock_boto_client.return_value = create_mock_dynamodb('batch_write_item')
    handler.clear_clients()
    events = [{'event_type': 'test', 'timestamp': '2025-01-01T00:00:00Z'}]
    session_context = {'user_agent': 'test', 'referrer': 'http://example.com'}
    event = _create_events_request(events, session_context)
    with patch.dict('os.environ', {'RACK_DESIGNER_EVENTS_TABLE': 'test-events-table'}):
        response = handler.handle_events(event)
    assert response['statusCode'] == 200


def test_lambda_handler_routes_events_post(handler):
    """Test lambda handler routes events POST correctly."""
    mock_return = {'statusCode': 200, 'body': '{}'}
    with patch.object(handler, 'handle_events', return_value=mock_return) as mock_h:
        event = {'httpMethod': 'POST', 'path': '/v1/sessions/abc/events', 'headers': {}}
        handler.lambda_handler(event, None)
        mock_h.assert_called_once()
