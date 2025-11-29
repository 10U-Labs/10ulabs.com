import json
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError


def test_generate_config_hash_returns_9_char_string(handler):
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    result = handler.generate_config_hash(config)
    assert len(result) == 9


def test_generate_config_hash_uses_only_valid_chars(handler):
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    result = handler.generate_config_hash(config)
    valid_chars = set('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    assert all(c in valid_chars for c in result)


def test_generate_config_hash_same_config_same_hash(handler):
    config1 = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    config2 = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    result1 = handler.generate_config_hash(config1)
    result2 = handler.generate_config_hash(config2)
    assert result1 == result2


def test_generate_config_hash_different_config_different_hash(handler):
    config1 = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    config2 = {'rackHeight': 24, 'rackCount': 3, 'placedParts': []}
    result1 = handler.generate_config_hash(config1)
    result2 = handler.generate_config_hash(config2)
    assert result1 != result2


def test_generate_config_hash_order_independent(handler):
    config1 = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    config2 = {'placedParts': [], 'rackCount': 3, 'rackHeight': 12}
    result1 = handler.generate_config_hash(config1)
    result2 = handler.generate_config_hash(config2)
    assert result1 == result2


def test_validate_rack_configuration_missing_rack_height(handler):
    config = {'rackCount': 3, 'placedParts': []}
    result = handler.validate_rack_configuration(config)
    assert result == 'Missing required field: rackHeight'


def test_validate_rack_configuration_missing_rack_count(handler):
    config = {'rackHeight': 12, 'placedParts': []}
    result = handler.validate_rack_configuration(config)
    assert result == 'Missing required field: rackCount'


def test_validate_rack_configuration_missing_placed_parts(handler):
    config = {'rackHeight': 12, 'rackCount': 3}
    result = handler.validate_rack_configuration(config)
    assert result == 'Missing required field: placedParts'


def test_validate_rack_configuration_invalid_rack_height_type(handler):
    config = {'rackHeight': '12', 'rackCount': 3, 'placedParts': []}
    result = handler.validate_rack_configuration(config)
    assert result == 'rackHeight must be an integer'


def test_validate_rack_configuration_invalid_rack_count_type(handler):
    config = {'rackHeight': 12, 'rackCount': '3', 'placedParts': []}
    result = handler.validate_rack_configuration(config)
    assert result == 'rackCount must be an integer'


def test_validate_rack_configuration_invalid_placed_parts_type(handler):
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': 'not a list'}
    result = handler.validate_rack_configuration(config)
    assert result == 'placedParts must be an array'


def test_validate_rack_configuration_rack_height_too_low(handler):
    config = {'rackHeight': 0, 'rackCount': 3, 'placedParts': []}
    result = handler.validate_rack_configuration(config)
    assert result == 'rackHeight must be between 1 and 42'


def test_validate_rack_configuration_rack_height_too_high(handler):
    config = {'rackHeight': 43, 'rackCount': 3, 'placedParts': []}
    result = handler.validate_rack_configuration(config)
    assert result == 'rackHeight must be between 1 and 42'


def test_validate_rack_configuration_rack_count_too_low(handler):
    config = {'rackHeight': 12, 'rackCount': 0, 'placedParts': []}
    result = handler.validate_rack_configuration(config)
    assert result == 'rackCount must be at least 1'


def test_validate_rack_configuration_valid_config_returns_none(handler):
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    result = handler.validate_rack_configuration(config)
    assert result is None


def test_handle_post_missing_configuration(handler):
    event = {'body': json.dumps({}), 'headers': {}}
    response = handler.handle_post(event)
    assert response['statusCode'] == 400


def test_handle_post_invalid_configuration(handler):
    event = {'body': json.dumps({'configuration': {'rackCount': 3, 'placedParts': []}}), 'headers': {}}
    response = handler.handle_post(event)
    assert response['statusCode'] == 400


@patch('boto3.client')
def test_handle_post_success(mock_boto_client, handler):
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.return_value = {}
    mock_boto_client.return_value = mock_dynamodb
    handler._clients.clear()
    event = {
        'body': json.dumps({'configuration': {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}}),
        'headers': {}
    }
    with patch.dict('os.environ', {'RACK_DESIGNER_CONFIGURATIONS_TABLE': 'test-table'}):
        response = handler.handle_post(event)
    assert response['statusCode'] == 200


def test_handle_get_missing_config_hash(handler):
    event = {'pathParameters': {}, 'headers': {}}
    response = handler.handle_get(event)
    assert response['statusCode'] == 400


def test_handle_get_invalid_config_hash_format(handler):
    event = {'pathParameters': {'config_hash': 'invalid'}, 'headers': {}}
    response = handler.handle_get(event)
    assert response['statusCode'] == 400


@patch('boto3.client')
def test_handle_get_not_found(mock_boto_client, handler):
    mock_dynamodb = MagicMock()
    mock_dynamodb.get_item.return_value = {}
    mock_boto_client.return_value = mock_dynamodb
    handler._clients.clear()
    event = {'pathParameters': {'config_hash': 'ABCD12345'}, 'headers': {}}
    with patch.dict('os.environ', {'RACK_DESIGNER_CONFIGURATIONS_TABLE': 'test-table'}):
        response = handler.handle_get(event)
    assert response['statusCode'] == 404


@patch('boto3.client')
def test_handle_get_success(mock_boto_client, handler):
    mock_dynamodb = MagicMock()
    mock_dynamodb.get_item.return_value = {
        'Item': {
            'config_hash': {'S': 'ABCD12345'},
            'configuration': {'S': json.dumps({'rackHeight': 12, 'rackCount': 3, 'placedParts': []})}
        }
    }
    mock_boto_client.return_value = mock_dynamodb
    handler._clients.clear()
    event = {'pathParameters': {'config_hash': 'ABCD12345'}, 'headers': {}}
    with patch.dict('os.environ', {'RACK_DESIGNER_CONFIGURATIONS_TABLE': 'test-table'}):
        response = handler.handle_get(event)
    assert response['statusCode'] == 200


def test_lambda_handler_options_returns_cors(handler):
    event = {'httpMethod': 'OPTIONS', 'path': '/v1/rack-designer/configurations'}
    response = handler.lambda_handler(event, None)
    assert response['statusCode'] == 200


def test_lambda_handler_routes_post(handler):
    with patch.object(handler, 'handle_post', return_value={'statusCode': 200, 'body': '{}'}) as mock_handler:
        event = {'httpMethod': 'POST', 'path': '/v1/rack-designer/configurations', 'headers': {}}
        handler.lambda_handler(event, None)
        mock_handler.assert_called_once()


def test_lambda_handler_routes_get(handler):
    with patch.object(handler, 'handle_get', return_value={'statusCode': 200, 'body': '{}'}) as mock_handler:
        event = {'httpMethod': 'GET', 'path': '/v1/rack-designer/configurations/ABCD12345', 'headers': {}}
        handler.lambda_handler(event, None)
        mock_handler.assert_called_once()


def test_lambda_handler_unknown_path_returns_404(handler):
    event = {'httpMethod': 'GET', 'path': '/v1/unknown', 'headers': {}}
    response = handler.lambda_handler(event, None)
    assert response['statusCode'] == 404


@patch('boto3.client')
def test_handle_post_with_device_id(mock_boto_client, handler):
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.return_value = {}
    mock_boto_client.return_value = mock_dynamodb
    handler._clients.clear()
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
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.return_value = {}
    mock_boto_client.return_value = mock_dynamodb
    handler._clients.clear()
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    with patch.dict('os.environ', {'RACK_DESIGNER_CONFIGURATIONS_TABLE': 'test-table'}):
        handler.save_rack_configuration('ABCD12345', config)
    call_args = mock_dynamodb.put_item.call_args
    item = call_args.kwargs['Item']
    assert 'created_at' in item


@patch('boto3.client')
def test_save_rack_configuration_stores_device_id(mock_boto_client, handler):
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.return_value = {}
    mock_boto_client.return_value = mock_dynamodb
    handler._clients.clear()
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    with patch.dict('os.environ', {'RACK_DESIGNER_CONFIGURATIONS_TABLE': 'test-table'}):
        handler.save_rack_configuration('ABCD12345', config, 'test-device-123')
    call_args = mock_dynamodb.put_item.call_args
    item = call_args.kwargs['Item']
    assert item['device_id'] == {'S': 'test-device-123'}


@patch('boto3.client')
def test_save_rack_configuration_without_device_id(mock_boto_client, handler):
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.return_value = {}
    mock_boto_client.return_value = mock_dynamodb
    handler._clients.clear()
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    with patch.dict('os.environ', {'RACK_DESIGNER_CONFIGURATIONS_TABLE': 'test-table'}):
        handler.save_rack_configuration('ABCD12345', config)
    call_args = mock_dynamodb.put_item.call_args
    item = call_args.kwargs['Item']
    assert 'device_id' not in item
