import base64
import json
from unittest.mock import MagicMock, patch

from test_fixtures.unit import (
    create_client_error,
    create_mock_dynamodb_client,
    reset_module_state,
)


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


def test_handle_post_missing_device_id(handler):
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    event = {
        'body': json.dumps({'configuration': config}),
        'headers': {}
    }
    response = handler.handle_post(event)
    assert response['statusCode'] == 400


def test_handle_post_missing_configuration(handler):
    event = {'body': json.dumps({'device_id': 'test-device'}), 'headers': {}}
    response = handler.handle_post(event)
    assert response['statusCode'] == 400


def test_handle_post_invalid_configuration(handler):
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
    mock_boto_client.return_value = create_mock_dynamodb_client('put_item')
    reset_module_state(handler, _clients={})
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
    event = {'pathParameters': {}, 'headers': {}}
    response = handler.handle_get(event)
    assert response['statusCode'] == 400


def test_handle_get_invalid_config_hash_format(handler):
    event = {'pathParameters': {'config_hash': 'invalid'}, 'headers': {}}
    response = handler.handle_get(event)
    assert response['statusCode'] == 400


def _run_handle_get(mock_boto_client, handler, return_item=None):
    mock_boto_client.return_value = create_mock_dynamodb_client('get_item', return_item)
    reset_module_state(handler, _clients={})
    event = {'pathParameters': {'config_hash': 'ABCD12345'}, 'headers': {}}
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        return handler.handle_get(event)


@patch('boto3.client')
def test_handle_get_not_found(mock_boto_client, handler):
    response = _run_handle_get(mock_boto_client, handler)
    assert response['statusCode'] == 404


@patch('boto3.client')
def test_handle_get_success(mock_boto_client, handler):
    config_json = json.dumps({'rackHeight': 12, 'rackCount': 3, 'placedParts': []})
    item = {'Item': {'config_hash': {'S': 'ABCD12345'}, 'configuration': {'S': config_json}}}
    response = _run_handle_get(mock_boto_client, handler, item)
    assert response['statusCode'] == 200


def test_lambda_handler_options_returns_cors(handler):
    event = {'httpMethod': 'OPTIONS', 'path': '/v1/rack-configurations'}
    response = handler.lambda_handler(event, None)
    assert response['statusCode'] == 200


def test_lambda_handler_routes_post(handler):
    mock_return = {'statusCode': 200, 'body': '{}'}
    with patch.object(handler, 'handle_post', return_value=mock_return) as mock_handler:
        event = {'httpMethod': 'POST', 'path': '/v1/rack-configurations', 'headers': {}}
        handler.lambda_handler(event, None)
        mock_handler.assert_called_once()
    assert True


def test_lambda_handler_routes_get(handler):
    mock_return = {'statusCode': 200, 'body': '{}'}
    with patch.object(handler, 'handle_get', return_value=mock_return) as mock_handler:
        event = {
            'httpMethod': 'GET',
            'path': '/v1/rack-configurations/ABCD12345',
            'headers': {}
        }
        handler.lambda_handler(event, None)
        mock_handler.assert_called_once()
    assert True


def test_lambda_handler_unknown_path_returns_404(handler):
    event = {'httpMethod': 'GET', 'path': '/v1/unknown', 'headers': {}}
    response = handler.lambda_handler(event, None)
    assert response['statusCode'] == 404


@patch('boto3.client')
def test_handle_post_with_device_id(mock_boto_client, handler):
    mock_boto_client.return_value = create_mock_dynamodb_client('put_item')
    reset_module_state(handler, _clients={})
    payload = {'configuration': {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}}
    payload['device_id'] = 'test-device-123'
    event = {'body': json.dumps(payload), 'headers': {}}
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        response = handler.handle_post(event)
    assert response['statusCode'] == 200


def _run_save_rack_configuration(mock_boto_client, handler, device_id=None):
    mock_dynamodb = create_mock_dynamodb_client('put_item')
    mock_boto_client.return_value = mock_dynamodb
    reset_module_state(handler, _clients={})
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        if device_id:
            handler.save_rack_configuration('ABCD12345', config, device_id)
        else:
            handler.save_rack_configuration('ABCD12345', config)
    return mock_dynamodb.put_item.call_args.kwargs['Item']


@patch('boto3.client')
def test_save_rack_configuration_stores_created_at(mock_boto_client, handler):
    item = _run_save_rack_configuration(mock_boto_client, handler)
    assert 'created_at' in item


@patch('boto3.client')
def test_save_rack_configuration_stores_device_id(mock_boto_client, handler):
    item = _run_save_rack_configuration(mock_boto_client, handler, 'test-device-123')
    assert item['device_id'] == {'S': 'test-device-123'}


@patch('boto3.client')
def test_save_rack_configuration_without_device_id(mock_boto_client, handler):
    item = _run_save_rack_configuration(mock_boto_client, handler)
    assert 'device_id' not in item


def test_parse_body_decodes_base64_when_flagged(handler):
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    encoded_body = base64.b64encode(json.dumps(config).encode('utf-8')).decode('utf-8')
    event = {'body': encoded_body, 'isBase64Encoded': True}
    result = handler.parse_body(event)
    assert result == config


def test_parse_body_returns_dict_when_not_base64(handler):
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    event = {'body': json.dumps(config), 'isBase64Encoded': False}
    result = handler.parse_body(event)
    assert result == config


def test_parse_body_returns_empty_dict_when_body_is_none(handler):
    event = {'body': None}
    result = handler.parse_body(event)
    assert result == {}


def test_parse_body_returns_empty_dict_when_body_is_empty_string(handler):
    event = {'body': ''}
    result = handler.parse_body(event)
    assert result == {}


def _create_save_error_mock(error_code):
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.side_effect = create_client_error(error_code, 'PutItem')
    return mock_dynamodb


def _run_save_with_error(mock_boto_client, handler, error_code):
    mock_boto_client.return_value = _create_save_error_mock(error_code)
    reset_module_state(handler, _clients={})
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        return handler.save_rack_configuration('ABCD12345', config)


@patch('boto3.client')
def test_save_rack_configuration_returns_success_on_conditional_check_failed(
    mock_boto_client, handler
):
    result = _run_save_with_error(
        mock_boto_client, handler, 'ConditionalCheckFailedException'
    )
    assert result == {'success': True, 'config_hash': 'ABCD12345'}


@patch('boto3.client')
def test_save_rack_configuration_returns_error_on_client_error(mock_boto_client, handler):
    result = _run_save_with_error(mock_boto_client, handler, 'InternalServerError')
    assert result['success'] is False


def _create_load_mock_with_item(config_hash, config):
    mock_dynamodb = MagicMock()
    mock_dynamodb.get_item.return_value = {
        'Item': {
            'config_hash': {'S': config_hash},
            'configuration': {'S': json.dumps(config)}
        }
    }
    mock_dynamodb.put_item.return_value = {}
    mock_dynamodb.delete_item.return_value = {}
    return mock_dynamodb


def _run_load_configuration(mock_boto_client, handler, config_hash, mock_dynamodb):
    mock_boto_client.return_value = mock_dynamodb
    reset_module_state(handler, _clients={})
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        return handler.load_rack_configuration(config_hash)


@patch('boto3.client')
def test_load_rack_configuration_returns_error_on_client_error(mock_boto_client, handler):
    mock_dynamodb = MagicMock()
    mock_dynamodb.get_item.side_effect = create_client_error('InternalServerError', 'GetItem')
    result = _run_load_configuration(mock_boto_client, handler, 'ABCD12345', mock_dynamodb)
    assert result['success'] is False


@patch('boto3.client')
def test_load_rack_configuration_triggers_migration_for_8_char_hash(
    mock_boto_client, handler
):
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    mock_dynamodb = _create_load_mock_with_item('ABCD1234', config)
    result = _run_load_configuration(mock_boto_client, handler, 'ABCD1234', mock_dynamodb)
    assert len(result.get('config_hash', '')) == 9


@patch('boto3.client')
def test_load_rack_configuration_skips_migration_for_9_char_hash(
    mock_boto_client, handler
):
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    mock_dynamodb = _create_load_mock_with_item('ABCD12345', config)
    result = _run_load_configuration(mock_boto_client, handler, 'ABCD12345', mock_dynamodb)
    assert result == {'success': True, 'config_hash': 'ABCD12345', 'configuration': config}


def _run_migrate(mock_boto_client, handler, old_hash, config, mock_dynamodb=None):
    if mock_dynamodb is None:
        mock_dynamodb = MagicMock()
        mock_dynamodb.put_item.return_value = {}
        mock_dynamodb.delete_item.return_value = {}
    mock_boto_client.return_value = mock_dynamodb
    reset_module_state(handler, _clients={})
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        return handler.migrate_rack_configuration(old_hash, config)


@patch('boto3.client')
def test_migrate_rack_configuration_returns_none_when_hash_unchanged(
    mock_boto_client, handler
):
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    new_hash = handler.generate_config_hash(config)
    result = _run_migrate(mock_boto_client, handler, new_hash, config)
    assert result is None


@patch('boto3.client')
def test_migrate_rack_configuration_returns_new_hash_on_success(
    mock_boto_client, handler
):
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    result = _run_migrate(mock_boto_client, handler, 'OLDHASH8', config)
    assert len(result) == 9


@patch('boto3.client')
def test_migrate_rack_configuration_returns_none_on_client_error(
    mock_boto_client, handler
):
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.side_effect = create_client_error('InternalServerError', 'PutItem')
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    result = _run_migrate(mock_boto_client, handler, 'OLDHASH8', config, mock_dynamodb)
    assert result is None


def test_error_response_includes_details_when_provided(handler):
    response = handler.error_response(500, 'Test error', 'Additional details')
    body = json.loads(response['body'])
    assert body['details'] == 'Additional details'


def test_error_response_omits_details_when_empty(handler):
    response = handler.error_response(400, 'Test error', '')
    body = json.loads(response['body'])
    assert 'details' not in body


def test_error_response_sets_correct_status_code(handler):
    response = handler.error_response(503, 'Service unavailable')
    assert response['statusCode'] == 503


def test_json_response_includes_cors_allow_origin(handler):
    response = handler.json_response(200, {'data': 'test'})
    assert response['headers']['Access-Control-Allow-Origin'] == '*'


def test_json_response_includes_cors_allow_methods(handler):
    response = handler.json_response(200, {'data': 'test'})
    assert 'GET' in response['headers']['Access-Control-Allow-Methods']


def test_json_response_sets_content_type_json(handler):
    response = handler.json_response(200, {'data': 'test'})
    assert response['headers']['Content-Type'] == 'application/json'


def _create_valid_post_event():
    return {
        'body': json.dumps({
            'configuration': {'rackHeight': 12, 'rackCount': 3, 'placedParts': []},
            'device_id': 'test-device'
        }),
        'headers': {}
    }


@patch('boto3.client')
def test_handle_post_returns_500_on_save_failure(mock_boto_client, handler):
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.side_effect = create_client_error('InternalServerError', 'PutItem')
    mock_boto_client.return_value = mock_dynamodb
    reset_module_state(handler, _clients={})
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        response = handler.handle_post(_create_valid_post_event())
    assert response['statusCode'] == 500


def test_handle_post_returns_500_on_value_error(handler):
    with patch.object(handler, 'generate_config_hash', side_effect=ValueError("test error")):
        response = handler.handle_post(_create_valid_post_event())
    assert response['statusCode'] == 500


def test_handle_post_value_error_includes_details(handler):
    with patch.object(handler, 'generate_config_hash', side_effect=ValueError("test error")):
        response = handler.handle_post(_create_valid_post_event())
    body = json.loads(response['body'])
    assert body['details'] == 'test error'


def test_handle_post_returns_500_on_key_error(handler):
    with patch.object(handler, 'generate_config_hash', side_effect=KeyError("missing_key")):
        response = handler.handle_post(_create_valid_post_event())
    assert response['statusCode'] == 500


def test_handle_post_key_error_includes_details(handler):
    with patch.object(handler, 'generate_config_hash', side_effect=KeyError("missing_key")):
        response = handler.handle_post(_create_valid_post_event())
    body = json.loads(response['body'])
    assert 'missing_key' in body['details']
