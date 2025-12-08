"""Unit tests for analytics event validation."""


def test_validate_analytics_event_valid(handler):
    """Test valid analytics event passes validation."""
    event = {'event_type': 'test', 'timestamp': '2025-01-01T00:00:00Z'}
    result = handler.validate_analytics_event(event)
    assert result is None


def test_validate_analytics_event_missing_event_type(handler):
    """Test validation fails without event_type."""
    event = {'timestamp': '2025-01-01T00:00:00Z'}
    result = handler.validate_analytics_event(event)
    assert result == 'Missing required field: event_type'


def test_validate_analytics_event_missing_timestamp(handler):
    """Test validation fails without timestamp."""
    event = {'event_type': 'test'}
    result = handler.validate_analytics_event(event)
    assert result == 'Missing required field: timestamp'


def test_validate_analytics_event_invalid_event_type_not_string(handler):
    """Test validation fails for non-string event_type."""
    event = {'event_type': 123, 'timestamp': '2025-01-01T00:00:00Z'}
    result = handler.validate_analytics_event(event)
    assert result == 'event_type must be a string'


def test_validate_analytics_event_invalid_timestamp_not_string(handler):
    """Test validation fails for non-string timestamp."""
    event = {'event_type': 'test', 'timestamp': 123}
    result = handler.validate_analytics_event(event)
    assert result == 'timestamp must be a string'


def test_validate_analytics_event_invalid_timestamp_format(handler):
    """Test validation fails for invalid timestamp format."""
    event = {'event_type': 'test', 'timestamp': 'not-a-date'}
    result = handler.validate_analytics_event(event)
    assert result == 'timestamp must be in ISO8601 format'


def test_validate_analytics_event_with_optional_fields(handler):
    """Test validation passes with optional fields."""
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
    """Test valid analytics request passes validation."""
    body = {
        'session_id': 'abc-123',
        'device_id': 'def-456',
        'events': [{'event_type': 'test', 'timestamp': '2025-01-01T00:00:00Z'}]
    }
    result = handler.validate_analytics_request(body)
    assert result is None


def test_validate_analytics_request_missing_session_id(handler):
    """Test validation fails without session_id."""
    body = {'device_id': 'def', 'events': []}
    result = handler.validate_analytics_request(body)
    assert result == 'Missing required field: session_id'


def test_validate_analytics_request_missing_device_id(handler):
    """Test validation fails without device_id."""
    body = {'session_id': 'abc', 'events': []}
    result = handler.validate_analytics_request(body)
    assert result == 'Missing required field: device_id'


def test_validate_analytics_request_missing_events(handler):
    """Test validation fails without events."""
    body = {'session_id': 'abc', 'device_id': 'def'}
    result = handler.validate_analytics_request(body)
    assert result == 'Missing required field: events'


def test_validate_analytics_request_session_id_not_string(handler):
    """Test validation fails for non-string session_id."""
    body = {'session_id': 123, 'device_id': 'def', 'events': []}
    result = handler.validate_analytics_request(body)
    assert result == 'session_id must be a string'


def test_validate_analytics_request_device_id_not_string(handler):
    """Test validation fails for non-string device_id."""
    body = {'session_id': 'abc', 'device_id': 123, 'events': []}
    result = handler.validate_analytics_request(body)
    assert result == 'device_id must be a string'


def test_validate_analytics_request_events_not_array(handler):
    """Test validation fails for non-array events."""
    body = {'session_id': 'abc', 'device_id': 'def', 'events': 'not-array'}
    result = handler.validate_analytics_request(body)
    assert result == 'events must be an array'


def test_validate_analytics_request_events_empty(handler):
    """Test validation fails for empty events array."""
    body = {'session_id': 'abc', 'device_id': 'def', 'events': []}
    result = handler.validate_analytics_request(body)
    assert result == 'events array cannot be empty'


def test_validate_analytics_request_events_too_many(handler):
    """Test validation fails for too many events."""
    events = [{'event_type': 'test', 'timestamp': '2025-01-01T00:00:00Z'}] * 26
    body = {'session_id': 'abc', 'device_id': 'def', 'events': events}
    result = handler.validate_analytics_request(body)
    assert result == 'events array cannot exceed 25 items'
