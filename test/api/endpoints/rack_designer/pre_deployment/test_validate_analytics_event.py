def test_validate_analytics_event_valid(handler):
    event = {'event_type': 'test', 'timestamp': '2025-01-01T00:00:00Z'}
    result = handler.validate_analytics_event(event)
    assert result is None


def test_validate_analytics_event_missing_event_type(handler):
    event = {'timestamp': '2025-01-01T00:00:00Z'}
    result = handler.validate_analytics_event(event)
    assert result == 'Missing required field: event_type'


def test_validate_analytics_event_missing_timestamp(handler):
    event = {'event_type': 'test'}
    result = handler.validate_analytics_event(event)
    assert result == 'Missing required field: timestamp'


def test_validate_analytics_event_invalid_event_type_not_string(handler):
    event = {'event_type': 123, 'timestamp': '2025-01-01T00:00:00Z'}
    result = handler.validate_analytics_event(event)
    assert result == 'event_type must be a string'


def test_validate_analytics_event_invalid_timestamp_not_string(handler):
    event = {'event_type': 'test', 'timestamp': 123}
    result = handler.validate_analytics_event(event)
    assert result == 'timestamp must be a string'


def test_validate_analytics_event_invalid_timestamp_format(handler):
    event = {'event_type': 'test', 'timestamp': 'not-a-date'}
    result = handler.validate_analytics_event(event)
    assert result == 'timestamp must be in ISO8601 format'


def test_validate_analytics_event_with_optional_fields(handler):
    event = {
        'event_type': 'part_added',
        'timestamp': '2025-01-01T00:00:00Z',
        'part_type': 'server',
        'rack_id': 1,
        'slot': 5
    }
    result = handler.validate_analytics_event(event)
    assert result is None


def test_validate_analytics_request_valid(handler):
    body = {
        'session_id': 'abc-123',
        'device_id': 'def-456',
        'events': [{'event_type': 'test', 'timestamp': '2025-01-01T00:00:00Z'}]
    }
    result = handler.validate_analytics_request(body)
    assert result is None


def test_validate_analytics_request_missing_session_id(handler):
    body = {'device_id': 'def', 'events': []}
    result = handler.validate_analytics_request(body)
    assert result == 'Missing required field: session_id'


def test_validate_analytics_request_missing_device_id(handler):
    body = {'session_id': 'abc', 'events': []}
    result = handler.validate_analytics_request(body)
    assert result == 'Missing required field: device_id'


def test_validate_analytics_request_missing_events(handler):
    body = {'session_id': 'abc', 'device_id': 'def'}
    result = handler.validate_analytics_request(body)
    assert result == 'Missing required field: events'


def test_validate_analytics_request_session_id_not_string(handler):
    body = {'session_id': 123, 'device_id': 'def', 'events': []}
    result = handler.validate_analytics_request(body)
    assert result == 'session_id must be a string'


def test_validate_analytics_request_device_id_not_string(handler):
    body = {'session_id': 'abc', 'device_id': 123, 'events': []}
    result = handler.validate_analytics_request(body)
    assert result == 'device_id must be a string'


def test_validate_analytics_request_events_not_array(handler):
    body = {'session_id': 'abc', 'device_id': 'def', 'events': 'not-array'}
    result = handler.validate_analytics_request(body)
    assert result == 'events must be an array'


def test_validate_analytics_request_events_empty(handler):
    body = {'session_id': 'abc', 'device_id': 'def', 'events': []}
    result = handler.validate_analytics_request(body)
    assert result == 'events array cannot be empty'


def test_validate_analytics_request_events_too_many(handler):
    events = [{'event_type': 'test', 'timestamp': '2025-01-01T00:00:00Z'}] * 26
    body = {'session_id': 'abc', 'device_id': 'def', 'events': events}
    result = handler.validate_analytics_request(body)
    assert result == 'events array cannot exceed 25 items'
