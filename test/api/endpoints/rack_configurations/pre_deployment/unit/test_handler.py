"""Unit tests for rack designer Lambda handler."""
import base64
import json
from unittest.mock import MagicMock, patch

from test_fixtures.unit import create_client_error, create_mock_dynamodb_client


def test_generate_config_hash_returns_9_char_string(handler):
    """Test that config hash is 9 characters."""
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    result = handler.generate_config_hash(config)
    assert len(result) == 9


def test_generate_config_hash_uses_only_valid_chars(handler):
    """Test that config hash uses only alphanumeric characters."""
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    result = handler.generate_config_hash(config)
    valid_chars = set('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    assert all(c in valid_chars for c in result)


def test_generate_config_hash_same_config_same_hash(handler):
    """Test that same config produces same hash."""
    config1 = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    config2 = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    result1 = handler.generate_config_hash(config1)
    result2 = handler.generate_config_hash(config2)
    assert result1 == result2


def test_generate_config_hash_different_config_different_hash(handler):
    """Test that different configs produce different hashes."""
    config1 = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    config2 = {'rackHeight': 24, 'rackCount': 3, 'placedParts': []}
    result1 = handler.generate_config_hash(config1)
    result2 = handler.generate_config_hash(config2)
    assert result1 != result2


def test_generate_config_hash_order_independent(handler):
    """Test that key order doesn't affect hash."""
    config1 = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    config2 = {'placedParts': [], 'rackCount': 3, 'rackHeight': 12}
    result1 = handler.generate_config_hash(config1)
    result2 = handler.generate_config_hash(config2)
    assert result1 == result2


def test_validate_rack_configuration_missing_rack_height(handler):
    """Test validation fails for missing rackHeight."""
    config = {'rackCount': 3, 'placedParts': []}
    result = handler.validate_rack_configuration(config)
    assert result == 'Missing required field: rackHeight'


def test_validate_rack_configuration_missing_rack_count(handler):
    """Test validation fails for missing rackCount."""
    config = {'rackHeight': 12, 'placedParts': []}
    result = handler.validate_rack_configuration(config)
    assert result == 'Missing required field: rackCount'


def test_validate_rack_configuration_missing_placed_parts(handler):
    """Test validation fails for missing placedParts."""
    config = {'rackHeight': 12, 'rackCount': 3}
    result = handler.validate_rack_configuration(config)
    assert result == 'Missing required field: placedParts'


def test_validate_rack_configuration_invalid_rack_height_type(handler):
    """Test validation fails for non-integer rackHeight."""
    config = {'rackHeight': '12', 'rackCount': 3, 'placedParts': []}
    result = handler.validate_rack_configuration(config)
    assert result == 'rackHeight must be an integer'


def test_validate_rack_configuration_invalid_rack_count_type(handler):
    """Test validation fails for non-integer rackCount."""
    config = {'rackHeight': 12, 'rackCount': '3', 'placedParts': []}
    result = handler.validate_rack_configuration(config)
    assert result == 'rackCount must be an integer'


def test_validate_rack_configuration_invalid_placed_parts_type(handler):
    """Test validation fails for non-array placedParts."""
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': 'not a list'}
    result = handler.validate_rack_configuration(config)
    assert result == 'placedParts must be an array'


def test_validate_rack_configuration_rack_height_too_low(handler):
    """Test validation fails for rackHeight below minimum."""
    config = {'rackHeight': 0, 'rackCount': 3, 'placedParts': []}
    result = handler.validate_rack_configuration(config)
    assert result == 'rackHeight must be between 1 and 42'


def test_validate_rack_configuration_rack_height_too_high(handler):
    """Test validation fails for rackHeight above maximum."""
    config = {'rackHeight': 43, 'rackCount': 3, 'placedParts': []}
    result = handler.validate_rack_configuration(config)
    assert result == 'rackHeight must be between 1 and 42'


def test_validate_rack_configuration_rack_count_too_low(handler):
    """Test validation fails for rackCount below minimum."""
    config = {'rackHeight': 12, 'rackCount': 0, 'placedParts': []}
    result = handler.validate_rack_configuration(config)
    assert result == 'rackCount must be at least 1'


def test_validate_rack_configuration_valid_config_returns_none(handler):
    """Test validation passes for valid config."""
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    result = handler.validate_rack_configuration(config)
    assert result is None


def test_handle_post_missing_device_id(handler):
    """Test POST returns 400 without device_id."""
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    event = {
        'body': json.dumps({'configuration': config}),
        'headers': {}
    }
    response = handler.handle_post(event)
    assert response['statusCode'] == 400


def test_handle_post_missing_configuration(handler):
    """Test POST returns 400 without configuration."""
    event = {'body': json.dumps({'device_id': 'test-device'}), 'headers': {}}
    response = handler.handle_post(event)
    assert response['statusCode'] == 400


def test_handle_post_invalid_configuration(handler):
    """Test POST returns 400 for invalid configuration."""
    event = {
        'body': json.dumps({
            'configuration': {'rackCount': 3, 'placedParts': []},
            'device_id': 'test-device'
        }),
        'headers': {}
    }
    response = handler.handle_post(event)
    assert response['statusCode'] == 400


@patch('boto3.client')
def test_handle_post_success(mock_boto_client, handler):
    """Test POST returns 200 for valid request."""
    mock_boto_client.return_value = create_mock_dynamodb_client('put_item')
    handler.clear_clients()
    event = {
        'body': json.dumps({
            'configuration': {'rackHeight': 12, 'rackCount': 3, 'placedParts': []},
            'device_id': 'test-device'
        }),
        'headers': {}
    }
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        response = handler.handle_post(event)
    assert response['statusCode'] == 200


def test_handle_get_missing_config_hash(handler):
    """Test GET returns 400 without config_hash."""
    event = {'pathParameters': {}, 'headers': {}}
    response = handler.handle_get(event)
    assert response['statusCode'] == 400


def test_handle_get_invalid_config_hash_format(handler):
    """Test GET returns 400 for invalid config_hash format."""
    event = {'pathParameters': {'config_hash': 'invalid'}, 'headers': {}}
    response = handler.handle_get(event)
    assert response['statusCode'] == 400


def _run_handle_get(mock_boto_client, handler, return_item=None):
    """Run handle_get with mocked DynamoDB and return response."""
    mock_boto_client.return_value = create_mock_dynamodb_client('get_item', return_item)
    handler.clear_clients()
    event = {'pathParameters': {'config_hash': 'ABCD12345'}, 'headers': {}}
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        return handler.handle_get(event)


@patch('boto3.client')
def test_handle_get_not_found(mock_boto_client, handler):
    """Test GET returns 404 when config not found."""
    response = _run_handle_get(mock_boto_client, handler)
    assert response['statusCode'] == 404


@patch('boto3.client')
def test_handle_get_success(mock_boto_client, handler):
    """Test GET returns 200 when config found."""
    config_json = json.dumps({'rackHeight': 12, 'rackCount': 3, 'placedParts': []})
    item = {'Item': {'config_hash': {'S': 'ABCD12345'}, 'configuration': {'S': config_json}}}
    response = _run_handle_get(mock_boto_client, handler, item)
    assert response['statusCode'] == 200


def test_lambda_handler_options_returns_cors(handler):
    """Test OPTIONS returns CORS headers."""
    event = {'httpMethod': 'OPTIONS', 'path': '/v1/rack-configurations'}
    response = handler.lambda_handler(event, None)
    assert response['statusCode'] == 200


def test_lambda_handler_routes_post(handler):
    """Test lambda handler routes POST requests correctly."""
    mock_return = {'statusCode': 200, 'body': '{}'}
    with patch.object(handler, 'handle_post', return_value=mock_return) as mock_handler:
        event = {'httpMethod': 'POST', 'path': '/v1/rack-configurations', 'headers': {}}
        handler.lambda_handler(event, None)
        mock_handler.assert_called_once()
    assert True  # Explicit pass


def test_lambda_handler_routes_get(handler):
    """Test lambda handler routes GET requests correctly."""
    mock_return = {'statusCode': 200, 'body': '{}'}
    with patch.object(handler, 'handle_get', return_value=mock_return) as mock_handler:
        event = {
            'httpMethod': 'GET',
            'path': '/v1/rack-configurations/ABCD12345',
            'headers': {}
        }
        handler.lambda_handler(event, None)
        mock_handler.assert_called_once()
    assert True  # Explicit pass


def test_lambda_handler_unknown_path_returns_404(handler):
    """Test lambda handler returns 404 for unknown paths."""
    event = {'httpMethod': 'GET', 'path': '/v1/unknown', 'headers': {}}
    response = handler.lambda_handler(event, None)
    assert response['statusCode'] == 404


@patch('boto3.client')
def test_handle_post_with_device_id(mock_boto_client, handler):
    """Test POST stores device_id correctly."""
    mock_boto_client.return_value = create_mock_dynamodb_client('put_item')
    handler.clear_clients()
    payload = {'configuration': {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}}
    payload['device_id'] = 'test-device-123'
    event = {'body': json.dumps(payload), 'headers': {}}
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        response = handler.handle_post(event)
    assert response['statusCode'] == 200


def _run_save_rack_configuration(mock_boto_client, handler, device_id=None):
    """Helper to run save_rack_configuration and return the stored item."""
    mock_dynamodb = create_mock_dynamodb_client('put_item')
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        if device_id:
            handler.save_rack_configuration('ABCD12345', config, device_id)
        else:
            handler.save_rack_configuration('ABCD12345', config)
    return mock_dynamodb.put_item.call_args.kwargs['Item']


@patch('boto3.client')
def test_save_rack_configuration_stores_created_at(mock_boto_client, handler):
    """Test save stores created_at timestamp."""
    item = _run_save_rack_configuration(mock_boto_client, handler)
    assert 'created_at' in item


@patch('boto3.client')
def test_save_rack_configuration_stores_device_id(mock_boto_client, handler):
    """Test save stores device_id when provided."""
    item = _run_save_rack_configuration(mock_boto_client, handler, 'test-device-123')
    assert item['device_id'] == {'S': 'test-device-123'}


@patch('boto3.client')
def test_save_rack_configuration_without_device_id(mock_boto_client, handler):
    """Test save omits device_id when not provided."""
    item = _run_save_rack_configuration(mock_boto_client, handler)
    assert 'device_id' not in item


# ============================================================================
# parse_body() tests
# ============================================================================


def test_parse_body_decodes_base64_when_flagged(handler):
    """Test parse_body decodes base64-encoded body when isBase64Encoded is True."""
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    encoded_body = base64.b64encode(json.dumps(config).encode('utf-8')).decode('utf-8')
    event = {'body': encoded_body, 'isBase64Encoded': True}
    result = handler.parse_body(event)
    assert result == config


def test_parse_body_returns_dict_when_not_base64(handler):
    """Test parse_body returns parsed JSON when isBase64Encoded is False."""
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    event = {'body': json.dumps(config), 'isBase64Encoded': False}
    result = handler.parse_body(event)
    assert result == config


def test_parse_body_returns_empty_dict_when_body_is_none(handler):
    """Test parse_body returns empty dict when body is None."""
    event = {'body': None}
    result = handler.parse_body(event)
    assert result == {}


def test_parse_body_returns_empty_dict_when_body_is_empty_string(handler):
    """Test parse_body returns empty dict when body is empty string."""
    event = {'body': ''}
    result = handler.parse_body(event)
    assert result == {}


# ============================================================================
# save_rack_configuration() error path tests
# ============================================================================


@patch('boto3.client')
def test_save_rack_configuration_returns_success_on_conditional_check_failed(
    mock_boto_client, handler
):
    """Test save returns success when config already exists (idempotent)."""
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.side_effect = create_client_error(
        'ConditionalCheckFailedException', 'PutItem'
    )
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        result = handler.save_rack_configuration('ABCD12345', config)
    assert result['success'] is True
    assert result['config_hash'] == 'ABCD12345'


@patch('boto3.client')
def test_save_rack_configuration_returns_error_on_client_error(mock_boto_client, handler):
    """Test save returns error dict when DynamoDB raises generic ClientError."""
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.side_effect = create_client_error(
        'InternalServerError', 'PutItem'
    )
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        result = handler.save_rack_configuration('ABCD12345', config)
    assert result['success'] is False
    assert 'error' in result


# ============================================================================
# load_rack_configuration() error path tests
# ============================================================================


@patch('boto3.client')
def test_load_rack_configuration_returns_error_on_client_error(mock_boto_client, handler):
    """Test load returns error dict when DynamoDB raises ClientError."""
    mock_dynamodb = MagicMock()
    mock_dynamodb.get_item.side_effect = create_client_error(
        'InternalServerError', 'GetItem'
    )
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        result = handler.load_rack_configuration('ABCD12345')
    assert result['success'] is False
    assert 'error' in result


@patch('boto3.client')
def test_load_rack_configuration_triggers_migration_for_8_char_hash(
    mock_boto_client, handler
):
    """Test load triggers migration when loading 8-char hash."""
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    config_json = json.dumps(config)
    mock_dynamodb = MagicMock()
    mock_dynamodb.get_item.return_value = {
        'Item': {'config_hash': {'S': 'ABCD1234'}, 'configuration': {'S': config_json}}
    }
    mock_dynamodb.put_item.return_value = {}
    mock_dynamodb.delete_item.return_value = {}
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        result = handler.load_rack_configuration('ABCD1234')
    assert result['success'] is True
    assert len(result['config_hash']) == 9


@patch('boto3.client')
def test_load_rack_configuration_skips_migration_for_9_char_hash(
    mock_boto_client, handler
):
    """Test load skips migration when loading 9-char hash."""
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    config_json = json.dumps(config)
    mock_dynamodb = MagicMock()
    mock_dynamodb.get_item.return_value = {
        'Item': {'config_hash': {'S': 'ABCD12345'}, 'configuration': {'S': config_json}}
    }
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        result = handler.load_rack_configuration('ABCD12345')
    assert result['success'] is True
    assert result['config_hash'] == 'ABCD12345'
    mock_dynamodb.put_item.assert_not_called()
    mock_dynamodb.delete_item.assert_not_called()


# ============================================================================
# migrate_rack_configuration() tests
# ============================================================================


@patch('boto3.client')
def test_migrate_rack_configuration_returns_none_when_hash_unchanged(
    mock_boto_client, handler
):
    """Test migrate returns None when new hash equals old hash."""
    mock_dynamodb = MagicMock()
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    new_hash = handler.generate_config_hash(config)
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        result = handler.migrate_rack_configuration(new_hash, config)
    assert result is None
    mock_dynamodb.put_item.assert_not_called()
    mock_dynamodb.delete_item.assert_not_called()


@patch('boto3.client')
def test_migrate_rack_configuration_returns_new_hash_on_success(
    mock_boto_client, handler
):
    """Test migrate returns new hash when migration succeeds."""
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.return_value = {}
    mock_dynamodb.delete_item.return_value = {}
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    old_hash = 'OLDHASH8'
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        result = handler.migrate_rack_configuration(old_hash, config)
    assert result is not None
    assert len(result) == 9
    mock_dynamodb.put_item.assert_called_once()
    mock_dynamodb.delete_item.assert_called_once()


@patch('boto3.client')
def test_migrate_rack_configuration_returns_none_on_client_error(
    mock_boto_client, handler
):
    """Test migrate returns None when DynamoDB raises ClientError."""
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.side_effect = create_client_error(
        'InternalServerError', 'PutItem'
    )
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    old_hash = 'OLDHASH8'
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        result = handler.migrate_rack_configuration(old_hash, config)
    assert result is None


# ============================================================================
# error_response() tests
# ============================================================================


def test_error_response_includes_details_when_provided(handler):
    """Test error_response includes details field when provided."""
    response = handler.error_response(500, 'Test error', 'Additional details')
    body = json.loads(response['body'])
    assert body['details'] == 'Additional details'


def test_error_response_omits_details_when_empty(handler):
    """Test error_response omits details field when empty string."""
    response = handler.error_response(400, 'Test error', '')
    body = json.loads(response['body'])
    assert 'details' not in body


def test_error_response_sets_correct_status_code(handler):
    """Test error_response sets the correct HTTP status code."""
    response = handler.error_response(503, 'Service unavailable')
    assert response['statusCode'] == 503


# ============================================================================
# json_response() tests
# ============================================================================


def test_json_response_includes_cors_headers(handler):
    """Test json_response includes CORS headers."""
    response = handler.json_response(200, {'data': 'test'})
    assert response['headers']['Access-Control-Allow-Origin'] == '*'
    assert 'GET' in response['headers']['Access-Control-Allow-Methods']
    assert 'POST' in response['headers']['Access-Control-Allow-Methods']


def test_json_response_sets_content_type_json(handler):
    """Test json_response sets Content-Type to application/json."""
    response = handler.json_response(200, {'data': 'test'})
    assert response['headers']['Content-Type'] == 'application/json'


# ============================================================================
# handle_post() error path tests
# ============================================================================


@patch('boto3.client')
def test_handle_post_returns_500_on_save_failure(mock_boto_client, handler):
    """Test POST returns 500 when save_rack_configuration fails."""
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.side_effect = create_client_error(
        'InternalServerError', 'PutItem'
    )
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    event = {
        'body': json.dumps({
            'configuration': {'rackHeight': 12, 'rackCount': 3, 'placedParts': []},
            'device_id': 'test-device'
        }),
        'headers': {}
    }
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        response = handler.handle_post(event)
    assert response['statusCode'] == 500


def test_handle_post_returns_500_on_value_error(handler):
    """Test POST returns 500 when ValueError is raised during processing."""
    event = {
        'body': json.dumps({
            'configuration': {'rackHeight': 12, 'rackCount': 3, 'placedParts': []},
            'device_id': 'test-device'
        }),
        'headers': {}
    }
    with patch.object(handler, 'generate_config_hash', side_effect=ValueError("test error")):
        response = handler.handle_post(event)
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert body['details'] == 'test error'


def test_handle_post_returns_500_on_key_error(handler):
    """Test POST returns 500 when KeyError is raised during processing."""
    event = {
        'body': json.dumps({
            'configuration': {'rackHeight': 12, 'rackCount': 3, 'placedParts': []},
            'device_id': 'test-device'
        }),
        'headers': {}
    }
    with patch.object(handler, 'generate_config_hash', side_effect=KeyError("missing_key")):
        response = handler.handle_post(event)
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'missing_key' in body['details']
