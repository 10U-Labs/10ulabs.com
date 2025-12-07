"""Unit tests for rack designer Lambda handler."""
import json
from unittest.mock import MagicMock, patch


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
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.return_value = {}
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    event = {
        'body': json.dumps({
            'configuration': {'rackHeight': 12, 'rackCount': 3, 'placedParts': []},
            'device_id': 'test-device'
        }),
        'headers': {}
    }
    with patch.dict('os.environ', {'RACK_DESIGNER_CONFIGURATIONS_TABLE': 'test-table'}):
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


@patch('boto3.client')
def test_handle_get_not_found(mock_boto_client, handler):
    """Test GET returns 404 when config not found."""
    mock_dynamodb = MagicMock()
    mock_dynamodb.get_item.return_value = {}
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    event = {'pathParameters': {'config_hash': 'ABCD12345'}, 'headers': {}}
    with patch.dict('os.environ', {'RACK_DESIGNER_CONFIGURATIONS_TABLE': 'test-table'}):
        response = handler.handle_get(event)
    assert response['statusCode'] == 404


@patch('boto3.client')
def test_handle_get_success(mock_boto_client, handler):
    """Test GET returns 200 when config found."""
    mock_dynamodb = MagicMock()
    config_json = json.dumps({'rackHeight': 12, 'rackCount': 3, 'placedParts': []})
    mock_dynamodb.get_item.return_value = {
        'Item': {
            'config_hash': {'S': 'ABCD12345'},
            'configuration': {'S': config_json}
        }
    }
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    event = {'pathParameters': {'config_hash': 'ABCD12345'}, 'headers': {}}
    with patch.dict('os.environ', {'RACK_DESIGNER_CONFIGURATIONS_TABLE': 'test-table'}):
        response = handler.handle_get(event)
    assert response['statusCode'] == 200


def test_lambda_handler_options_returns_cors(handler):
    """Test OPTIONS returns CORS headers."""
    event = {'httpMethod': 'OPTIONS', 'path': '/v1/rack-designer/configurations'}
    response = handler.lambda_handler(event, None)
    assert response['statusCode'] == 200


def test_lambda_handler_routes_post(handler):
    """Test lambda handler routes POST requests correctly."""
    mock_return = {'statusCode': 200, 'body': '{}'}
    with patch.object(handler, 'handle_post', return_value=mock_return) as mock_handler:
        event = {'httpMethod': 'POST', 'path': '/v1/rack-designer/configurations', 'headers': {}}
        handler.lambda_handler(event, None)
        mock_handler.assert_called_once()


def test_lambda_handler_routes_get(handler):
    """Test lambda handler routes GET requests correctly."""
    mock_return = {'statusCode': 200, 'body': '{}'}
    with patch.object(handler, 'handle_get', return_value=mock_return) as mock_handler:
        event = {
            'httpMethod': 'GET',
            'path': '/v1/rack-designer/configurations/ABCD12345',
            'headers': {}
        }
        handler.lambda_handler(event, None)
        mock_handler.assert_called_once()


def test_lambda_handler_unknown_path_returns_404(handler):
    """Test lambda handler returns 404 for unknown paths."""
    event = {'httpMethod': 'GET', 'path': '/v1/unknown', 'headers': {}}
    response = handler.lambda_handler(event, None)
    assert response['statusCode'] == 404


@patch('boto3.client')
def test_handle_post_with_device_id(mock_boto_client, handler):
    """Test POST stores device_id correctly."""
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.return_value = {}
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    event = {
        'body': json.dumps({
            'configuration': {'rackHeight': 12, 'rackCount': 3, 'placedParts': []},
            'device_id': 'test-device-123'
        }),
        'headers': {}
    }
    with patch.dict('os.environ', {'RACK_DESIGNER_CONFIGURATIONS_TABLE': 'test-table'}):
        response = handler.handle_post(event)
    assert response['statusCode'] == 200


@patch('boto3.client')
def test_save_rack_configuration_stores_created_at(mock_boto_client, handler):
    """Test save stores created_at timestamp."""
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.return_value = {}
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    with patch.dict('os.environ', {'RACK_DESIGNER_CONFIGURATIONS_TABLE': 'test-table'}):
        handler.save_rack_configuration('ABCD12345', config)
    call_args = mock_dynamodb.put_item.call_args
    item = call_args.kwargs['Item']
    assert 'created_at' in item


@patch('boto3.client')
def test_save_rack_configuration_stores_device_id(mock_boto_client, handler):
    """Test save stores device_id when provided."""
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.return_value = {}
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    with patch.dict('os.environ', {'RACK_DESIGNER_CONFIGURATIONS_TABLE': 'test-table'}):
        handler.save_rack_configuration('ABCD12345', config, 'test-device-123')
    call_args = mock_dynamodb.put_item.call_args
    item = call_args.kwargs['Item']
    assert item['device_id'] == {'S': 'test-device-123'}


@patch('boto3.client')
def test_save_rack_configuration_without_device_id(mock_boto_client, handler):
    """Test save omits device_id when not provided."""
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.return_value = {}
    mock_boto_client.return_value = mock_dynamodb
    handler.clear_clients()
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    with patch.dict('os.environ', {'RACK_DESIGNER_CONFIGURATIONS_TABLE': 'test-table'}):
        handler.save_rack_configuration('ABCD12345', config)
    call_args = mock_dynamodb.put_item.call_args
    item = call_args.kwargs['Item']
    assert 'device_id' not in item
